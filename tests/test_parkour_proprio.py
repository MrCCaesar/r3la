"""Shared history and action contracts using the installed native manager seam."""

from types import SimpleNamespace

import pytest
import torch

from isaaclab.managers import ObservationManager

from r3la.tasks.velocity.config.Unitree.parkour_env_cfg import UnitreeGo2ParkourEnvCfg
from r3la.tasks.velocity.mdp.actions import validate_parkour_actions

CANONICAL = [f"{leg}_{joint}_joint" for leg in ("FL", "FR", "RL", "RR") for joint in ("hip", "thigh", "calf")]


def test_config_uses_five_unscaled_frames_and_official_action_mapping():
    cfg = UnitreeGo2ParkourEnvCfg()
    group = cfg.observations.proprio
    assert group.history_length == 5 and group.history_order == "time"
    assert group.concatenate_terms and group.flatten_history_dim and group.enable_corruption
    for name in ("base_ang_vel", "projected_gravity", "joint_pos", "joint_vel", "last_actions"):
        term = getattr(group, name)
        assert term.clip is None and term.scale is None
    assert not cfg.observations.commands.enable_corruption
    assert not cfg.observations.privilege.enable_corruption
    assert not cfg.observations.target.enable_corruption
    action = cfg.actions.joint_pos
    assert action.joint_names == CANONICAL and action.preserve_order
    assert action.scale == 0.5 and action.clip is None and action.use_default_offset
    command = cfg.commands.base_velocity
    assert command.resampling_time_range[0] > cfg.episode_length_s
    assert command.initial_speed == 1 and command.evaluation_velocity is None


@pytest.mark.parametrize("shape", [(), (12,), (1, 12), (2, 11), (2, 12, 1)])
def test_action_checks_reject_bad_shapes_before_native_broadcast(shape):
    with pytest.raises(ValueError, match="shape"):
        validate_parkour_actions(SimpleNamespace(num_envs=2, device="cpu"), torch.zeros(shape))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_action_checks_reject_nonfinite_values(value):
    action = torch.zeros(2, 12)
    action[0, 2] = value
    with pytest.raises(ValueError, match="finite"):
        validate_parkour_actions(SimpleNamespace(num_envs=2, device="cpu"), action)


def test_action_checks_reject_wrong_dtype_device_and_accept_finite_unclipped_values():
    env = SimpleNamespace(num_envs=2, device="cpu")
    for dtype in (torch.int64, torch.float64):
        with pytest.raises(TypeError, match="float32"):
            validate_parkour_actions(env, torch.zeros(2, 12, dtype=dtype))
    with pytest.raises(TypeError, match="Tensor"):
        validate_parkour_actions(env, [[0.0] * 12] * 2)
    with pytest.raises(ValueError, match="device"):
        validate_parkour_actions(env, torch.zeros(2, 12, device="meta"))
    validate_parkour_actions(env, torch.full((2, 12), 2.0))


class AssetBoundary:
    """External simulator state with intentionally reversed native joint order."""

    def __init__(self):
        self.joint_names = list(reversed(CANONICAL))
        self.num_joints = 12
        relative = torch.arange(12, dtype=torch.float32).repeat(2, 1)
        self.data = SimpleNamespace(
            joint_pos=SimpleNamespace(torch=relative + 100),
            default_joint_pos=SimpleNamespace(torch=torch.full((2, 12), 100.0)),
            joint_vel=SimpleNamespace(torch=relative * 2 + 50),
            default_joint_vel=SimpleNamespace(torch=torch.full((2, 12), 50.0)),
            root_ang_vel_b=SimpleNamespace(torch=torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])),
            projected_gravity_b=SimpleNamespace(torch=torch.tensor([[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]])),
        )

    def find_joints(self, names, preserve_order=False):
        selected = [name for name in (names if preserve_order else self.joint_names) if name in names]
        return [self.joint_names.index(name) for name in selected], selected


def manager_fixture():
    cfg = UnitreeGo2ParkourEnvCfg()
    asset = AssetBoundary()
    env = SimpleNamespace(
        num_envs=2,
        device="cpu",
        sim=SimpleNamespace(is_playing=lambda: True),
        scene={"robot": asset},
        action_manager=SimpleNamespace(action=torch.zeros(2, 12)),
        command_manager=SimpleNamespace(get_command=lambda name: torch.tensor([[0.2, 0, 0], [0.7, 0, 0]])),
    )
    manager = ObservationManager({"proprio": cfg.observations.proprio, "commands": cfg.observations.commands}, env)
    return env, manager


def test_native_history_backfill_shared_sample_noise_and_canonical_order():
    env, manager = manager_fixture()
    obs = manager.compute(update_history=True)
    history = obs["proprio"].reshape(2, 5, 42)
    assert obs["commands"].shape == (2, 3)
    torch.testing.assert_close(history, history[:, :1].expand(-1, 5, -1), rtol=0, atol=0)
    frame = history[:, -1]
    relative = torch.arange(11, -1, -1, dtype=torch.float32).expand(2, -1)
    clean = torch.cat(
        (
            env.scene["robot"].data.root_ang_vel_b.torch,
            env.scene["robot"].data.projected_gravity_b.torch,
            relative,
            relative * 2,
            env.action_manager.action,
        ),
        dim=-1,
    )
    noise_limit = torch.tensor([0.2] * 3 + [0.05] * 3 + [0.01] * 12 + [1.5] * 12 + [0.0] * 12)
    assert torch.all((frame - clean).abs() <= noise_limit + 1e-6)
    # Actor and WM/decoder consumers select from the same returned data, no resampling.
    encoder = obs["proprio"].reshape(2, 5, 42)[:, -1, :30]
    decoder_target = history[:, -1, :30]
    torch.testing.assert_close(encoder, decoder_target, rtol=0, atol=0)
    assert encoder.data_ptr() == decoder_target.data_ptr()


def test_time_order_and_selected_reset_keep_other_rows_history():
    env, manager = manager_fixture()
    first = manager.compute(update_history=True)["proprio"].reshape(2, 5, 42).clone()
    env.action_manager.action[:] = 0.25
    second = manager.compute(update_history=True)["proprio"].reshape(2, 5, 42).clone()
    torch.testing.assert_close(second[:, :-1], first[:, 1:], rtol=0, atol=0)
    torch.testing.assert_close(second[:, -1, 30:], torch.full((2, 12), 0.25), rtol=0, atol=0)
    manager.reset(torch.tensor([0]))
    env.action_manager.action[0] = 0
    third = manager.compute(update_history=True)["proprio"].reshape(2, 5, 42)
    torch.testing.assert_close(third[0], third[0, :1].expand(5, -1), rtol=0, atol=0)
    torch.testing.assert_close(third[1, :-1], second[1, 1:], rtol=0, atol=0)


def test_reading_recorded_history_does_not_append_or_expose_a_fresh_draw():
    env, manager = manager_fixture()
    initial = manager.compute(update_history=True)["proprio"].clone()
    env.action_manager.action[:] = 0.5
    reread = manager.compute(update_history=False)["proprio"]
    torch.testing.assert_close(reread, initial, rtol=0, atol=0)


def test_foot_sensor_names_keep_the_same_canonical_leg_mapping():
    cfg = UnitreeGo2ParkourEnvCfg()
    for name, foot in (("fl", "FL"), ("fr", "FR"), ("rl", "RL"), ("rr", "RR")):
        scanner = getattr(cfg.scene, name + "_height_scanner")
        assert scanner.prim_path.endswith("/" + foot + "_foot")
