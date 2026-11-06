# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for the project's task registrations."""

import gymnasium as gym

import r3la.tasks  # noqa: F401


def test_task_registrations():
    """The project tasks must expose valid environment and agent entry points."""
    spec = gym.spec("R3la-SWAP-Parkour-UnitreeGo2")
    assert spec.entry_point == "isaaclab.envs:ManagerBasedRLEnv"
    from isaaclab_tasks.utils import load_cfg_from_registry

    from r3la.labs.terrains.terrain_importer import ParkourTerrainImporter

    cfg = load_cfg_from_registry(spec.id, "env_cfg_entry_point")
    assert cfg.scene.terrain.class_type is ParkourTerrainImporter
    assert set(cfg.scene.terrain.terrain_generator.sub_terrains) == {
        "box",
        "gap",
        "stairs",
        "tilted_stairs",
        "side_slope",
        "rough_grid",
    }


def test_registered_generator_allocates_all_six_approved_family_column_counts():
    from isaaclab_tasks.utils import load_cfg_from_registry

    from r3la.labs.terrains.terrain_generator import ParkourTerrainGenerator

    cfg = load_cfg_from_registry("R3la-SWAP-Parkour-UnitreeGo2", "env_cfg_entry_point")
    terrain_cfg = cfg.scene.terrain.terrain_generator.copy()
    terrain_cfg.num_rows = 1
    terrain_cfg.border_width = 0
    terrain_cfg.color_scheme = "none"
    terrain = ParkourTerrainGenerator(terrain_cfg, device="cpu")
    assert [r.layout.family for r in terrain.task_regions[0]] == (
        ["box"] * 4 + ["gap"] * 4 + ["stairs"] * 2 + ["tilted_stairs"] * 4 + ["side_slope"] * 4 + ["rough_grid"] * 2
    )
