"""Deterministic evaluation changes settings while retaining task behavior."""

import pytest

from r3la.tasks.velocity.config.Unitree.evaluation import make_parkour_evaluation_cfg


def test_evaluation_fixes_assignment_command_and_nominal_dynamics_without_noise():
    cfg = make_parkour_evaluation_cfg("tilted_stairs", level=9, velocity=1.5, mirror_sign=-1, seed=42)
    generator = cfg.scene.terrain.terrain_generator
    assert generator.num_rows == 10 and generator.num_cols == 1 and generator.curriculum
    assert list(generator.sub_terrains) == ["tilted_stairs"]
    assert generator.sub_terrains["tilted_stairs"].mirror_sign == -1
    assert cfg.commands.base_velocity.evaluation_velocity == 1.5
    assert cfg.curriculum.terrain_levels is None
    assert cfg.events.reset_base.params["nominal"]
    assert cfg.events.evaluation_terrain.params["level"] == 9
    assert cfg.events.base_com is None and cfg.events.base_mass is None and cfg.events.actuator_gains is None
    assert cfg.events.physics_material.params["nominal"]
    assert cfg.observations.privilege.com_offsets.params["event_name"] is None
    for name in ("proprio", "privilege", "target", "commands", "amp", "metadata"):
        assert not getattr(cfg.observations, name).enable_corruption
    assert cfg.observations.proprio.history_length == 5
    assert cfg.terminations.parkour_attempt is not None and not cfg.compute_final_obs


@pytest.mark.parametrize(
    "kwargs",
    [
        {"family": "unknown"},
        {"level": 10},
        {"level": -1},
        {"level": 1.5},
        {"mirror_sign": -1},
        {"velocity": -1},
        {"velocity": float("nan")},
    ],
)
def test_evaluation_rejects_invalid_selection(kwargs):
    with pytest.raises(ValueError):
        make_parkour_evaluation_cfg(**kwargs)
