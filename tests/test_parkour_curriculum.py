"""Native curriculum/command lifecycle seams with synthetic terrain families."""

from types import SimpleNamespace as NS

import pytest
import torch

from isaaclab.managers import CurriculumTermCfg

from r3la.tasks.velocity.mdp.commands import ParkourVelocityCommand, ParkourVelocityCommandCfg
from r3la.tasks.velocity.mdp.curriculums import ParkourCurriculum


def fixture(levels=3):
    terrain = NS(
        terrain_levels=torch.zeros(2, dtype=torch.int64),
        terrain_types=torch.tensor([0, 1]),
        task_family_id=torch.tensor([[0, 1]] * levels),
        terrain_origins=torch.arange(levels * 6, dtype=torch.float32).reshape(levels, 2, 3),
        env_origins=torch.zeros(2, 3),
    )
    attempt = NS(
        ending=torch.ones(2, dtype=torch.bool),
        success=torch.ones(2, dtype=torch.bool),
        duration=torch.ones(2),
        tracking_integral=torch.ones(2),
    )
    command_cfg = ParkourVelocityCommandCfg(resampling_time_range=(20.02, 20.02))
    env = NS(
        num_envs=2,
        device="cpu",
        scene=NS(terrain=terrain),
        step_dt=0.02,
        max_episode_length_s=20.0,
        command_manager=NS(get_term=lambda name: NS(cfg=command_cfg)),
        termination_manager=NS(get_term_cfg=lambda name: NS(func=attempt)),
    )
    term = ParkourCurriculum(CurriculumTermCfg(func=ParkourCurriculum), env)
    env.curriculum_manager = NS(cfg=NS(terrain_levels=NS(func=term)))
    return env, term, attempt


def test_curricula_need_twenty_attempts_and_ignore_manual_reset():
    env, term, attempt = fixture()
    for _ in range(19):
        term(env, torch.tensor([1, 0]))
    assert env.scene.terrain.terrain_levels.tolist() == [0, 0]
    assert term.speed_upper_bounds.tolist() == [1.0] * 6
    term(env, torch.tensor([1, 0]))
    assert env.scene.terrain.terrain_levels.tolist() == [1, 1]
    torch.testing.assert_close(term.speed_upper_bounds[:2], torch.tensor([1.1, 1.1]))
    assert len(term.speed_batches[0]) == 0
    term.reset(torch.tensor([0, 1]))  # windows and bounds persist across native resets
    attempt.ending[:] = False
    term(env, torch.tensor([0, 1]))
    assert len(term.terrain_windows[0][0]) == 20


def test_commands_use_updated_family_bound_only_on_next_native_reset():
    env, curriculum, _ = fixture()
    cfg = ParkourVelocityCommandCfg(resampling_time_range=(20.02, 20.02))
    command = ParkourVelocityCommand(cfg, env)
    command.reset()
    before = command.command.clone()
    curriculum.speed_upper_bounds[0] = 2.0
    for _ in range(1000):
        command.compute(0.02)
    torch.testing.assert_close(command.command, before, rtol=0, atol=0)
    command.reset(torch.tensor([0]))
    assert 0 <= command.command[0, 0] <= 2
    torch.testing.assert_close(command.command[1], before[1])
    assert torch.count_nonzero(command.command[:, 1:]) == 0
    with pytest.raises(ValueError, match="episode"):
        ParkourVelocityCommand(ParkourVelocityCommandCfg(resampling_time_range=(20.0, 20.0)), env)


def test_simultaneous_rows_are_sorted_and_family_windows_are_independent():
    env, term, attempt = fixture()
    env.scene.terrain.task_family_id[:, 1] = 0
    attempt.duration[:] = 0.5
    for i in range(19):
        attempt.success[0] = i < 15
        term(env, torch.tensor([0]))
    attempt.success[:] = torch.tensor([True, False])
    term(env, torch.tensor([1, 0]))
    assert env.scene.terrain.terrain_levels.tolist() == [1, 0]  # 16/20, then 16/21
    assert len(term.terrain_windows[0][0]) == 21
    assert len(term.terrain_windows[1][0]) == 0
    assert not term.speed_batches[0]  # all attempts were too short


@pytest.mark.parametrize("successes,expected", [(16, 2), (6, 0), (7, 1), (15, 1)])
def test_terrain_inclusive_thresholds_at_twenty_attempts(successes, expected):
    env, term, attempt = fixture()
    attempt.duration[:] = .5
    for i in range(20):
        env.scene.terrain.terrain_levels[0] = 1
        attempt.success[0] = i < successes
        term(env, torch.tensor([0]))
    assert env.scene.terrain.terrain_levels[0] == expected


@pytest.mark.parametrize("levels", [1, 3])
def test_top_level_recycle_excludes_highest_and_rolling_window_is_bounded(levels):
    env, term, attempt = fixture(levels)
    terrain = env.scene.terrain
    terrain.terrain_levels[:] = levels - 1
    for _ in range(20):
        term(env, torch.tensor([0]))
    assert 0 <= terrain.terrain_levels[0] < max(1, levels - 1)
    attempt.success[:] = False
    for _ in range(110):
        terrain.terrain_levels[:] = 0
        term(env, torch.tensor([0]))
    assert len(term.terrain_windows[0][0]) == 100
    assert term.terrain_success_rate[0, 0] == 0
    assert terrain.terrain_levels[0] == 0


def test_velocity_batches_include_failures_equal_weight_actual_duration_and_clamp():
    env, term, attempt = fixture()
    attempt.success[:] = False
    attempt.duration[:] = 0.99
    term(env, torch.tensor([0]))
    assert not term.speed_batches[0]
    attempt.duration[0] = 0.9999996  # exactly 50 float32 control intervals
    attempt.tracking_integral[0] = attempt.duration[0]
    for _ in range(19):
        term(env, torch.tensor([0]))
    attempt.duration[0], attempt.tracking_integral[0] = 20.0, 0.0
    term(env, torch.tensor([0]))  # equal-attempt mean .95 despite long failure
    assert term.speed_upper_bounds[0] == pytest.approx(1.1)
    assert not term.speed_batches[0] and term.speed_upper_bounds[1] == 1
    term.speed_upper_bounds[0] = 3
    attempt.duration[0], attempt.tracking_integral[0] = 1.0, 1.0
    for _ in range(20):
        term(env, torch.tensor([0]))
    assert term.speed_upper_bounds[0] == 3
    attempt.tracking_integral[0] = 0.3
    for _ in range(20):
        term(env, torch.tensor([0]))
    assert term.speed_upper_bounds[0] == pytest.approx(2.9)


@pytest.mark.parametrize(
    "kwargs", [{"initial_speed": -1}, {"max_speed": 0.5}, {"initial_speed": float("nan")}, {"evaluation_velocity": 4}]
)
def test_command_configuration_rejects_invalid_speed_bounds(kwargs):
    env, _, _ = fixture()
    with pytest.raises(ValueError):
        ParkourVelocityCommand(ParkourVelocityCommandCfg(**kwargs), env)
