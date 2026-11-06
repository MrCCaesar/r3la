"""Synthetic physical transitions through the approved native attempt-term seam."""

from types import SimpleNamespace

import pytest
import torch

from isaaclab.managers import TerminationTermCfg

from r3la.tasks.velocity.mdp.attempts import ParkourAttemptState


def proxy(tensor):
    return SimpleNamespace(torch=tensor)


def make_env():
    n = 2
    state = SimpleNamespace(
        root_pos_w=proxy(torch.tensor([[2.0, 5.0, 0.4], [2.0, 5.0, 0.4]])),
        root_quat_w=proxy(torch.tensor([[0.0, 0.0, 0.0, 1.0]]).repeat(n, 1)),
        root_lin_vel_w=proxy(torch.zeros(n, 3)),
        root_lin_vel_b=proxy(torch.zeros(n, 3)),
        root_ang_vel_b=proxy(torch.zeros(n, 3)),
    )
    terrain = SimpleNamespace(
        terrain_levels=torch.zeros(n, dtype=torch.int64),
        terrain_types=torch.zeros(n, dtype=torch.int64),
        task_tile_to_world=torch.eye(4).reshape(1, 1, 4, 4),
        task_legal_xy=torch.tensor([[[[1.0, 4.0], [4.5, 6.0]]]]),
        task_completion_xy=torch.tensor([[[[3.15, 4.4], [4.35, 5.6]]]]),
        task_support_xy=torch.tensor([[[[3.0, 4.25], [4.5, 5.75]]]]),
        task_support_normal=torch.tensor([[[0.0, 0.0, 1.0]]]),
        task_support_offset=torch.tensor([[-0.6]]),
        task_gates=torch.tensor([[[[3.0, 4.25, 5.75]]]]),
        task_gate_count=torch.tensor([[1]]),
    )
    sensor_data = SimpleNamespace(
        contact_pos_w=proxy(torch.full((n, 5, 1, 3), float("nan"))),
        normal_force_matrix_w=proxy(torch.zeros(n, 5, 1, 3)),
        net_normal_forces_w_history=proxy(torch.zeros(n, 4, 5, 3)),
    )
    sensor = SimpleNamespace(
        data=sensor_data,
        find_bodies=lambda names, preserve_order=True: ([4], ["base"]) if names == "base" else ([0, 1, 2, 3], names),
    )

    class Scene(dict):
        pass

    scene = Scene(robot=SimpleNamespace(data=state), contact_forces=sensor)
    scene.terrain = terrain
    env = SimpleNamespace(
        num_envs=n,
        device="cpu",
        step_dt=0.02,
        common_step_counter=0,
        scene=scene,
        episode_length_buf=torch.zeros(n, dtype=torch.int64),
        max_episode_length=1000,
        command_manager=SimpleNamespace(get_command=lambda name: torch.zeros(n, 3)),
    )
    term = ParkourAttemptState(TerminationTermCfg(func=ParkourAttemptState), env)
    term.reset()
    return env, term


def transition(env, term, x, support=False):
    env.scene["robot"].data.root_pos_w.torch[:, 0] = x
    data = env.scene["contact_forces"].data
    data.normal_force_matrix_w.torch[:, :2, 0, 2] = 2 if support else 0
    data.contact_pos_w.torch[:, :2, 0] = torch.tensor([3.5, 5, 0.6])
    env.common_step_counter += 1
    env.episode_length_buf += 1
    return term(env)


def test_airborne_entry_needs_ten_intervals_of_landing_evidence():
    env, term = make_env()
    assert not transition(env, term, 3.5).any()
    for _ in range(8):
        assert not transition(env, term, 3.5, support=True).any()
    assert transition(env, term, 3.5, support=True).all()
    assert term.success.all()
    duration = term.duration.clone()
    term(env)
    torch.testing.assert_close(term.duration, duration, rtol=0, atol=0)


@pytest.mark.parametrize("failure", ["timeout", "base"])
def test_failure_overrides_coincident_landing(failure):
    env, term = make_env()
    for _ in range(9):
        transition(env, term, 3.5, support=True)
    if failure == "timeout":
        env.episode_length_buf[:] = 999
    else:
        env.scene["contact_forces"].data.net_normal_forces_w_history.torch[:, 3, 4, 0] = 2
    transition(env, term, 3.5, support=True)
    assert not term.success.any()
    assert term.ending.all()


def test_wrong_surface_and_retreat_cannot_complete():
    env, term = make_env()
    transition(env, term, 3.5, support=True)
    data = env.scene["contact_forces"].data
    for _ in range(15):
        # Native contact point is on the ground, not the box top.
        data.contact_pos_w.torch[:, :2, 0] = torch.tensor([3.5, 5, 0])
        env.common_step_counter += 1
        term(env)
    assert not term.success.any()
    transition(env, term, 2.5)
    assert (term.gate_progress == 0).all()


def test_outside_span_crossing_is_bypass_and_manual_reset_is_not_an_attempt():
    env, term = make_env()
    env.scene["robot"].data.root_pos_w.torch[:, 1] = 4.1
    transition(env, term, 2.0)
    assert transition(env, term, 3.5).all()
    assert term.bypass.all() and not term.success.any()
    term.reset(torch.tensor([0]))
    assert not term.ending[0] and term.ending[1]
    assert term.duration[0] == 0


def contact_step(env, term, feet, point=None):
    env.scene["robot"].data.root_pos_w.torch[:, 0] = 3.5
    data = env.scene["contact_forces"].data
    data.normal_force_matrix_w.torch.zero_()
    data.normal_force_matrix_w.torch[:, feet, 0, 2] = 2
    data.contact_pos_w.torch[:, :, 0] = torch.tensor([3.5, 5.0, 0.6] if point is None else point)
    env.common_step_counter += 1
    env.episode_length_buf += 1
    return term(env)


@pytest.mark.parametrize(
    ("samples", "feet", "expected"),
    [
        ([0, 1, 2, 3, 9], [0, 1], True),
        ([0, 1, 2, 9], [0, 1], False),
        (list(range(10)), [0], False),
        (list(range(9)), [0, 1], False),
    ],
)
def test_landing_support_occupancy_distinct_feet_and_final_sample(samples, feet, expected):
    env, term = make_env()
    for i in range(10):
        contact_step(env, term, feet if i in samples else [])
    assert bool(term.success.all()) is expected


def test_nohit_and_stale_support_cannot_complete():
    env, term = make_env()
    for _ in range(10):
        contact_step(env, term, [0, 1], [float("nan")] * 3)
    assert not term.success.any()
    for _ in range(4):
        contact_step(env, term, [0, 1])
    for _ in range(10):
        contact_step(env, term, [])
    contact_step(env, term, [0, 1])
    assert not term.success.any()


@pytest.mark.parametrize(
    ("roll_degrees", "vertical", "expected"),
    [
        (29.0, 0.5, True),
        (31.0, 0.0, False),
        (0.0, 0.5001, False),
        (-31.0, 0.0, False),
    ],
)
def test_attitude_and_vertical_velocity_limits(roll_degrees, vertical, expected):
    import math

    from isaaclab.utils.math import quat_from_euler_xyz

    env, term = make_env()
    zero = torch.zeros(2)
    env.scene["robot"].data.root_quat_w.torch[:] = quat_from_euler_xyz(
        torch.full((2,), math.radians(roll_degrees)), zero, zero
    )
    env.scene["robot"].data.root_lin_vel_w.torch[:, 2] = vertical
    for _ in range(10):
        contact_step(env, term, [0, 1])
    assert bool(term.success.all()) is expected


def test_multiple_high_speed_gates_and_later_gate_rollback():
    env, term = make_env()
    terrain = env.scene.terrain
    terrain.task_gates = torch.tensor([[[[3.0, 4.25, 5.75], [4.0, 4.25, 5.75]]]])
    terrain.task_gate_count[:] = 2
    transition(env, term, 4.25)
    assert (term.gate_progress == 2).all()
    transition(env, term, 3.5)
    assert (term.gate_progress == 1).all()
    transition(env, term, 2.5)
    assert (term.gate_progress == 0).all()


def test_tracking_includes_ending_step_and_partial_reset_preserves_other_row():
    env, term = make_env()
    transition(env, term, 2.5)
    env.episode_length_buf[:] = 999
    transition(env, term, 2.5)
    torch.testing.assert_close(term.duration, torch.full((2,), 0.04))
    torch.testing.assert_close(term.tracking_integral, torch.full((2,), 0.04))
    assert term.ending.all()
    term.reset(torch.tensor([0]))
    assert term.duration[0] == 0 and term.duration[1] == pytest.approx(0.04)
    assert term.tracking_integral[0] == 0 and term.tracking_integral[1] == pytest.approx(0.04)


@pytest.mark.parametrize("surface", ["landing", "floor", "wall"])
def test_gap_passage_requires_far_landing_support(surface):
    env, term = make_env()
    terrain = env.scene.terrain
    # Approved d=1 gap, independent literals also check the common detector's contract.
    terrain.task_legal_xy = torch.tensor([[[[1.0, 4.0], [5.8, 6.0]]]])
    terrain.task_completion_xy = torch.tensor([[[[3.95, 4.15], [5.65, 5.85]]]])
    terrain.task_support_xy = torch.tensor([[[[3.8, 4.0], [5.8, 6.0]]]])
    terrain.task_support_offset[:] = 0
    terrain.task_gates = torch.tensor([[[[3.0, 4.0, 6.0], [3.8, 4.0, 6.0]]]])
    terrain.task_gate_count[:] = 2
    point = {"landing": [4.8, 5, 0], "floor": [3.4, 5, -1], "wall": [3.8, 5, -0.5]}[surface]
    data = env.scene["contact_forces"].data
    data.normal_force_matrix_w.torch[:, :2, 0, 2] = 2
    data.contact_pos_w.torch[:, :2, 0] = torch.tensor(point)
    env.scene["robot"].data.root_pos_w.torch[:, 0] = 4.8
    for _ in range(10):
        env.common_step_counter += 1
        term(env)
    assert (term.gate_progress == 2).all()
    assert bool(term.success.all()) is (surface == "landing")
    env.scene["robot"].data.root_pos_w.torch[:, 0] = 3.5
    env.common_step_counter += 1
    term(env)
    assert (term.gate_progress == 1).all()
    env.scene["robot"].data.root_pos_w.torch[:, 0] = 2.5
    env.common_step_counter += 1
    term(env)
    assert (term.gate_progress == 0).all()
    env.scene["robot"].data.root_pos_w.torch[:, 1] = 6.1
    env.common_step_counter += 1
    term(env)
    assert term.bypass.all() and not term.success.any()


@pytest.mark.parametrize("contact_surface", ["platform", "highest_tread"])
def test_stair_completion_requires_actual_platform_support(contact_surface):
    env, term = make_env()
    terrain = env.scene.terrain
    terrain.task_legal_xy = torch.tensor([[[[1.0, 4.0], [7.0, 6.0]]]])
    terrain.task_completion_xy = torch.tensor([[[[6.15, 3.15], [6.85, 6.85]]]])
    terrain.task_support_xy = torch.tensor([[[[6.0, 3.0], [7.0, 7.0]]]])
    terrain.task_support_offset[:] = -2.53
    terrain.task_gates = torch.tensor([[[[3.0, 4.0, 6.0], [6.0, 4.0, 6.0]]]])
    terrain.task_gate_count[:] = 2
    data = env.scene["contact_forces"].data
    data.normal_force_matrix_w.torch[:, :2, 0, 2] = 2
    data.contact_pos_w.torch[:, :2, 0] = torch.tensor(
        [6.5, 5, 2.53] if contact_surface == "platform" else [5.85, 5, 2.3]
    )
    env.scene["robot"].data.root_pos_w.torch[:, 0] = 6.5
    for _ in range(10):
        env.common_step_counter += 1
        term(env)
    assert (term.gate_progress == 2).all()
    assert bool(term.success.all()) is (contact_surface == "platform")
    # Platform width does not widen the legal two-metre route.
    env.scene["robot"].data.root_pos_w.torch[:, 1] = 3.5
    env.common_step_counter += 1
    term(env)
    assert term.bypass.all() and not term.success.any()


@pytest.mark.parametrize("surface", ["landing", "slope"])
def test_side_slope_passage_requires_far_flat_support(surface):
    env, term = make_env()
    terrain = env.scene.terrain
    terrain.task_legal_xy = torch.tensor([[[[1.0, 4.0], [7.0, 6.0]]]])
    terrain.task_completion_xy = torch.tensor([[[[5.15, 4.15], [6.85, 5.85]]]])
    terrain.task_support_xy = torch.tensor([[[[5.0, 4.0], [7.0, 6.0]]]])
    terrain.task_support_offset[:] = 0
    terrain.task_gates = torch.tensor([[[[3.0, 4.0, 6.0], [5.0, 4.0, 6.0]]]])
    terrain.task_gate_count[:] = 2
    data = env.scene["contact_forces"].data
    data.normal_force_matrix_w.torch[:, :2, 0, 2] = 2
    data.contact_pos_w.torch[:, :2, 0] = torch.tensor([6.0, 5.0, 0.0] if surface == "landing" else [4.0, 5.5, 0.181985])
    env.scene["robot"].data.root_pos_w.torch[:, 0] = 6.0
    for _ in range(10):
        env.common_step_counter += 1
        term(env)
    assert (term.gate_progress == 2).all()
    assert bool(term.success.all()) is (surface == "landing")
    env.scene["robot"].data.root_pos_w.torch[:, 0] = 4.5
    env.common_step_counter += 1
    term(env)
    assert (term.gate_progress == 1).all()
    env.scene["robot"].data.root_pos_w.torch[:, 1] = 6.1
    env.common_step_counter += 1
    term(env)
    assert term.bypass.all() and not term.success.any()


@pytest.mark.parametrize("surface", ["landing", "cell"])
def test_rough_grid_crossing_requires_far_flat_support(surface):
    env, term = make_env()
    terrain = env.scene.terrain
    terrain.task_legal_xy = torch.tensor([[[[1.0, 4.0], [7.0, 6.0]]]])
    terrain.task_completion_xy = torch.tensor([[[[5.15, 4.15], [6.85, 5.85]]]])
    terrain.task_support_xy = torch.tensor([[[[5.0, 4.0], [7.0, 6.0]]]])
    terrain.task_support_offset[:] = 0
    terrain.task_gates = torch.tensor([[[[3.0, 4.0, 6.0], [5.0, 4.0, 6.0]]]])
    terrain.task_gate_count[:] = 2
    data = env.scene["contact_forces"].data
    data.normal_force_matrix_w.torch[:, :2, 0, 2] = 2
    data.contact_pos_w.torch[:, :2, 0] = torch.tensor([6.0, 5.0, 0.0] if surface == "landing" else [4.1, 5.1, 0.1])
    env.scene["robot"].data.root_pos_w.torch[:, 0] = 6.0
    for _ in range(10):
        env.common_step_counter += 1
        term(env)
    assert (term.gate_progress == 2).all()
    assert bool(term.success.all()) is (surface == "landing")
    env.scene["robot"].data.root_pos_w.torch[:, 0] = 4.5
    env.common_step_counter += 1
    term(env)
    assert (term.gate_progress == 1).all()
    env.scene["robot"].data.root_pos_w.torch[:, 1] = 6.1
    env.common_step_counter += 1
    term(env)
    assert term.bypass.all() and not term.success.any()
