"""Approved terrain layout/mesh/generator seams, without a simulator."""

import numpy as np
import pytest
import trimesh

from r3la.labs.terrains.layouts import build_terrain_layout
from r3la.labs.terrains.trimesh.mesh_terrains_cfg import ParkourSubTerrainCfg


@pytest.mark.parametrize(("difficulty", "height"), [(0.0, 0.1), (1.0, 0.6)])
def test_box_mesh_and_task_regions_share_geometry(difficulty, height):
    cfg = ParkourSubTerrainCfg(seed=7)
    layout = build_terrain_layout(difficulty, cfg)
    meshes, origin = cfg.function(difficulty, cfg)
    mesh = trimesh.util.concatenate(meshes)
    np.testing.assert_allclose(layout.spawn_pos, [2, 5, 0])
    np.testing.assert_allclose(layout.completion_xy, [[3.15, 4.4], [4.35, 5.6]])
    np.testing.assert_allclose(layout.support_surface.xy_bounds, [[3, 4.25], [4.5, 5.75]])
    assert mesh.bounds[1, 2] == pytest.approx(height)
    assert layout.support_surface.offset == pytest.approx(-height)
    assert origin[2] == pytest.approx(height)
    assert all(m.is_watertight and m.volume > 0 for m in meshes)


def test_invalid_layout_fails_with_context():
    for difficulty in [-0.1, 1.1, float("nan")]:
        with pytest.raises(ValueError, match="box"):
            build_terrain_layout(difficulty, ParkourSubTerrainCfg())


def test_generator_cache_preserves_sample_and_world_placement(tmp_path):
    from isaaclab.terrains import TerrainGeneratorCfg

    from r3la.labs.terrains.terrain_generator import ParkourTerrainGenerator

    cfg = TerrainGeneratorCfg(
        class_type=ParkourTerrainGenerator,
        seed=7,
        size=(10, 10),
        num_rows=2,
        num_cols=1,
        border_width=0,
        curriculum=True,
        use_cache=True,
        cache_dir=str(tmp_path),
        color_scheme="none",
        sub_terrains={"box": ParkourSubTerrainCfg()},
    )
    first = ParkourTerrainGenerator(cfg, device="cpu")
    second = ParkourTerrainGenerator(cfg, device="cpu")
    for row in range(2):
        a, b = first.task_regions[row, 0], second.task_regions[row, 0]
        assert a.layout.canonical_id == b.layout.canonical_id
        assert row / 2 <= a.layout.difficulty < (row + 1) / 2
        np.testing.assert_allclose(a.tile_to_world[:3, 3], [-10 + row * 10, -5, 0])
    np.testing.assert_allclose(first.terrain_mesh.vertices, second.terrain_mesh.vertices, atol=1e-6)
    np.testing.assert_array_equal(first.terrain_mesh.faces, second.terrain_mesh.faces)
    cfg.use_cache = False
    uncached = ParkourTerrainGenerator(cfg, device="cpu")
    np.testing.assert_allclose(first.terrain_mesh.vertices, uncached.terrain_mesh.vertices, atol=1e-6)
    assert first.terrain_mesh.metadata["r3la_task_regions"].shape == (2, 1)


@pytest.mark.parametrize("selection", ["tensor", "slice"])
def test_partial_reset_uses_assigned_spawn_and_only_writes_selected_rows(selection):
    from types import SimpleNamespace
    from unittest.mock import Mock

    import torch

    from r3la.tasks.velocity.mdp.events import reset_parkour_state

    robot = Mock()
    robot.data.default_joint_pos = torch.ones((2, 12))
    terrain = SimpleNamespace(
        task_spawn_pos=torch.tensor([[[12.0, 25.0, 0.0]], [[32.0, 45.0, 0.0]]]),
        task_spawn_yaw=torch.zeros((2, 1)),
        terrain_levels=torch.tensor([0, 1]),
        terrain_types=torch.tensor([0, 0]),
    )

    class Scene(dict):
        pass

    scene = Scene(robot=robot)
    scene.terrain = terrain
    env = SimpleNamespace(scene=scene, num_envs=2, device="cpu", _parkour_spawn_radius=0.7)
    ids = torch.tensor([1])
    reset_parkour_state(env, ids if selection == "tensor" else slice(1, 2))
    pose = robot.write_root_pose_to_sim.call_args.args[0]
    assert pose.shape == (1, 7)
    assert 31.8 <= pose[0, 0] <= 32.2
    assert 44.8 <= pose[0, 1] <= 45.2
    assert pose[0, 2] == pytest.approx(0.4)
    assert torch.linalg.vector_norm(pose[0, 3:]) == pytest.approx(1)
    assert torch.count_nonzero(robot.write_root_velocity_to_sim.call_args.args[0]) == 0
    joints, velocity = robot.write_joint_state_to_sim.call_args.args
    assert torch.all((joints >= 0.9) & (joints <= 1.1))
    assert torch.count_nonzero(velocity) == 0
    for method in [robot.write_root_pose_to_sim, robot.write_root_velocity_to_sim, robot.write_joint_state_to_sim]:
        assert torch.equal(method.call_args.kwargs["env_ids"], ids)


def test_layout_rejects_bad_regions_gates_and_placement():
    from dataclasses import replace

    from r3la.labs.terrains.layouts import Gate, PlacedTerrainLayout

    layout = build_terrain_layout(0.5, ParkourSubTerrainCfg())
    for changes in (
        {"spawn_pos": [float("nan"), 5, 0]},
        {"completion_xy": [[0.1, 0.1], [0.2, 0.2]]},
        {"gates": (Gate(3, np.array([4.25, 5.75])), Gate(2, np.array([4.25, 5.75])))},
        {"support_surface": replace(layout.support_surface, normal=np.array([0, 0, 2]))},
    ):
        with pytest.raises(ValueError, match="box terrain"):
            replace(layout, **changes)
    with pytest.raises(ValueError, match="placement"):
        PlacedTerrainLayout(layout, 0, 0, np.zeros((4, 4)))


def test_entire_spawn_footprint_and_jitter_must_fit_approach():
    layout = build_terrain_layout(0, ParkourSubTerrainCfg())
    layout.validate_spawn_footprint(0.7)
    with pytest.raises(ValueError, match="footprint"):
        layout.validate_spawn_footprint(0.81)


def test_box_geometry_metadata_must_match_support_surface():
    from dataclasses import replace

    from r3la.labs.terrains.layouts import BoxGeometry

    layout = build_terrain_layout(0.5, ParkourSubTerrainCfg())
    with pytest.raises(ValueError, match="box terrain"):
        BoxGeometry(0.35, np.array([float("nan")]))
    with pytest.raises(ValueError, match="box terrain"):
        replace(layout, geometry=BoxGeometry(0.9, layout.geometry.top_bounds))
