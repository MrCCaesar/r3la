"""S67 numeric fixtures at reward and clean-state observation boundaries."""

from types import SimpleNamespace as NS

import pytest
import torch

from isaaclab.managers import RewardManager, SceneEntityCfg
from isaaclab.utils.string import resolve_matching_names

from r3la.tasks.velocity.config.Unitree.parkour_env_cfg import RewardsCfg
from r3la.tasks.velocity.mdp.observations import terrain_relative_height
from r3la.tasks.velocity.mdp.rewards import (
    action_smoothness_l2,
    base_height_l2,
    feet_air_time,
    flat_orientation_l2,
    stance_base_height_orientation_exp,
    undesired_contacts,
)


def fixture():
    def proxy(value):
        return NS(torch=torch.tensor(value, dtype=torch.float32))

    state = NS(root_quat_w=proxy([[0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0]]))
    forces = torch.zeros(2, 4, 3)
    forces[..., 2] = 2
    contact = NS(
        net_normal_forces_w=NS(torch=forces),
        net_normal_forces_w_history=NS(torch=torch.zeros(2, 4, 4, 3)),
        last_air_time=proxy([[0.7, 0.4, 0.5, 0.8], [0.3, 0.3, 0.3, 0.3]]),
    )
    sensor = NS(data=contact, compute_first_contact=lambda dt: NS(torch=torch.tensor([[True, True, False, False]] * 2)))
    scan = NS(
        read_sample=lambda: NS(
            values=torch.tensor([[0.3, 0.5], [0.0, 0.0]]), valid=torch.tensor([[True, True], [False, False]])
        )
    )
    return NS(
        scene={"robot": NS(data=state), "contact_forces": sensor, "terrain_height_scanner": scan},
        command_manager=NS(get_command=lambda name: torch.zeros(2, 3)),
        step_dt=0.02,
        num_envs=2,
        device="cpu",
    )


def test_height_masks_and_stance_use_terrain_relative_height_without_invalid_fallback():
    env = fixture()
    height, valid = terrain_relative_height(env)
    torch.testing.assert_close(height, torch.tensor([[0.4], [0.0]]))
    assert valid.tolist() == [[True], [False]]
    torch.testing.assert_close(base_height_l2(env, 0.4), torch.zeros(2))
    torch.testing.assert_close(stance_base_height_orientation_exp(env, 0.4, 0.1, 0.1), torch.tensor([1.0, 0.0]))


def test_collision_counts_history_once_but_airtime_has_no_low_command_gate_or_clamp():
    env = fixture()
    env.scene["contact_forces"].data.net_normal_forces_w_history.torch[0, :, 0, 2] = 2
    env.scene["contact_forces"].data.net_normal_forces_w_history.torch[0, 0, 1, 0] = 3
    cfg = SceneEntityCfg("contact_forces")
    torch.testing.assert_close(undesired_contacts(env, 1.0, cfg), torch.tensor([2.0, 0.0]))
    torch.testing.assert_close(feet_air_time(env, cfg, 0.5), torch.tensor([0.1, -0.4]))


def test_orientation_uses_world_euler_angles_and_action_second_difference_starts_immediately():
    env = fixture()
    env.scene["robot"].data.root_quat_w.torch[0] = torch.tensor([0.5, 0.0, 0.0, 0.8660254])
    assert flat_orientation_l2(env)[0].item() == pytest.approx(1.0966227, abs=1e-5)
    env.action_manager = NS(action=torch.ones(2, 12), prev_action=torch.zeros(2, 12))
    term = action_smoothness_l2(NS(), env)
    torch.testing.assert_close(term(env), torch.full((2,), 12.0))
    env.action_manager.prev_action.fill_(1)
    env.action_manager.action.fill_(3)
    torch.testing.assert_close(term(env), torch.full((2,), 12.0))
    term.reset(torch.tensor([0]))
    env.action_manager.prev_action[0] = 0
    env.action_manager.action[0] = 2
    env.action_manager.prev_action[1] = 3
    env.action_manager.action[1] = 4
    torch.testing.assert_close(term(env), torch.tensor([48.0, 12.0]))


class Entity:
    """External simulator state implementing native scene lookup contracts."""

    def __init__(self, data):
        self.data = data
        self.joint_names = [
            f"{leg}_{joint}_joint" for leg in ("FL", "FR", "RL", "RR") for joint in ("hip", "thigh", "calf")
        ]
        self.body_names = [
            f"{leg}_{link}" for link in ("thigh", "calf", "foot") for leg in ("FL", "FR", "RL", "RR")
        ] + ["base"]
        self.num_joints, self.num_bodies = 12, 13

    def find_joints(self, names, preserve_order=False):
        return resolve_matching_names(names, self.joint_names, preserve_order=preserve_order)

    def find_bodies(self, names, preserve_order=False):
        return resolve_matching_names(names, self.body_names, preserve_order=preserve_order)

    def compute_first_contact(self, dt):
        return NS(torch=torch.ones(2, 13, dtype=torch.bool))


def test_all_s67_raw_terms_weights_and_native_dt_once():
    def proxy(x):
        return NS(torch=x)

    state = NS(
        root_lin_vel_b=proxy(torch.tensor([[0.2, -0.1, 0.3]]).repeat(2, 1)),
        root_ang_vel_b=proxy(torch.tensor([[0.4, -0.2, 0.1]]).repeat(2, 1)),
        root_quat_w=proxy(torch.tensor([[0.0, 0.0, 0.0, 1.0]]).repeat(2, 1)),
        joint_pos=proxy(torch.full((2, 12), 0.1)),
        default_joint_pos=proxy(torch.zeros(2, 12)),
        joint_vel=proxy(torch.full((2, 12), 2.0)),
        applied_torque=proxy(torch.full((2, 12), 3.0)),
        joint_acc=proxy(torch.full((2, 12), 4.0)),
    )
    history = torch.zeros(2, 4, 13, 3)
    history[:, :, 0, 2] = 2  # count once despite all four physics samples
    forces = torch.zeros(2, 13, 3)
    forces[:, 8, 0], forces[:, 8, 2] = 5, 1
    contact = NS(
        net_normal_forces_w_history=proxy(history),
        net_forces_w=proxy(forces),
        net_normal_forces_w=proxy(torch.zeros_like(forces)),
        last_air_time=proxy(torch.full((2, 13), 0.7)),
    )
    env = fixture()
    env.scene["robot"], env.scene["contact_forces"] = Entity(state), Entity(contact)
    env.scene["robot"].actuators = NS(applied_effort=state.applied_torque)
    env.scene["terrain_height_scanner"].read_sample = lambda: NS(
        values=torch.full((2, 187), 0.5), valid=torch.ones(2, 187, dtype=torch.bool)
    )
    env.sim = NS(is_playing=lambda: True)
    env.action_manager = NS(action=torch.full((2, 12), 0.2), prev_action=torch.full((2, 12), 0.1))
    env.command_manager.get_command = lambda name: torch.tensor([[0.5, 0.0, 0.0]]).repeat(2, 1)
    manager = RewardManager(RewardsCfg(), env)
    expected = [
        ("track_lin_vel_xy_exp", 0.51341712, 1.0),
        ("track_ang_vel_z_exp", 0.93550699, 0.5),
        ("base_height_stance_exp", 0.0, 1.0),
        ("feet_air_time", 0.8, 0.5),
        ("base_height_l2", 0.01, -5.0),
        ("lin_vel_z_l2", 0.09, -1.0),
        ("ang_vel_xy_l2", 0.2, -0.05),
        ("flat_orientation_l2", 0.0, -0.2),
        ("undesired_contacts", 1.0, -1.0),
        ("feet_stumble", 1.0, -0.1),
        ("hip_abad_pos", 0.04, -1.0),
        ("dof_torques_l2", 108.0, -1e-6),
        ("dof_acc_l2", 192.0, -5e-7),
        ("mechanical_joint_power", 72.0, -1e-6),
        ("action_rate_l2", 0.12, -0.01),
        ("action_smooth_l2", 0.0, -0.004),
    ]
    assert manager.active_terms == [name for name, _, _ in expected]
    for name, raw, weight in expected:
        term = manager.get_term_cfg(name)
        assert term.weight == weight
        torch.testing.assert_close(term.func(env, **term.params), torch.full((2,), raw), atol=1e-5, rtol=1e-5)
    # Fresh manager: raw probes above may advance the stateful smoothness term.
    manager = RewardManager(RewardsCfg(), env)
    torch.testing.assert_close(
        manager.compute(dt=0.02), torch.full((2,), sum(raw * w for _, raw, w in expected) * 0.02), atol=1e-6, rtol=1e-5
    )
