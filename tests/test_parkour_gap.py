"""Gap geometry and task contracts through approved public generation seams."""

from dataclasses import replace

import numpy as np
import pytest
import trimesh

from r3la.labs.terrains.layouts import build_terrain_layout
from r3la.labs.terrains.trimesh.mesh_terrains_cfg import ParkourGapTerrainCfg


@pytest.mark.parametrize(("difficulty", "width", "far"), [(0.0, 0.2, 3.2), (1.0, 0.8, 3.8)])
def test_gap_floor_walls_and_landing_agree_with_task_regions(difficulty, width, far):
    cfg = ParkourGapTerrainCfg(seed=7)
    layout = build_terrain_layout(difficulty, cfg)
    meshes, origin = cfg.function(difficulty, cfg)
    mesh = trimesh.util.concatenate(meshes)
    assert layout.geometry.width == pytest.approx(width)
    assert layout.geometry.depth == 1
    assert len(layout.gates) == 2
    assert layout.gates[1].x == pytest.approx(far)
    np.testing.assert_allclose(layout.support_surface.xy_bounds, [[far, 4], [far + 2, 6]])
    np.testing.assert_allclose(layout.completion_xy, [[far + 0.15, 4.15], [far + 1.85, 5.85]])
    np.testing.assert_allclose(origin, [far + 1, 5, 0])
    assert all(m.is_watertight and m.volume > 0 for m in meshes)
    # Downward rays prove no flat ground masks the ditch; wall rays prove real collision surfaces.
    starts = [[3 + width / 2, 5, 1], [3 + width / 2, 5, -0.5], [3 + width / 2, 5, -0.5], [far + 1, 5, 1]]
    directions = [[0, 0, -1], [0, 1, 0], [1, 0, 0], [0, 0, -1]]
    hits, rays, _ = mesh.ray.intersects_location(starts, directions, multiple_hits=False)
    hits = hits[np.argsort(rays)]
    np.testing.assert_allclose(
        hits, [[3 + width / 2, 5, -1], [3 + width / 2, 6, -0.5], [far, 5, -0.5], [far + 1, 5, 0]], atol=1e-7
    )


@pytest.mark.parametrize("size", [(5, 10), (10, 6), (6, 6)])
def test_gap_rejects_small_tiles_and_inconsistent_support(size):
    with pytest.raises(ValueError, match="gap terrain"):
        build_terrain_layout(1, ParkourGapTerrainCfg(size=size))
    layout = build_terrain_layout(1, ParkourGapTerrainCfg())
    with pytest.raises(ValueError, match="gap terrain"):
        replace(layout, support_surface=replace(layout.support_surface, offset=1))


def test_box_gap_cache_and_world_placement_share_pipeline(tmp_path):
    from isaaclab.terrains import TerrainGeneratorCfg

    from r3la.labs.terrains.terrain_generator import ParkourTerrainGenerator
    from r3la.labs.terrains.trimesh.mesh_terrains_cfg import ParkourSubTerrainCfg

    cfg = TerrainGeneratorCfg(
        class_type=ParkourTerrainGenerator,
        seed=17,
        size=(10.0, 10.0),
        num_rows=2,
        num_cols=2,
        border_width=0,
        curriculum=True,
        use_cache=True,
        cache_dir=str(tmp_path),
        color_scheme="none",
        sub_terrains={"box": ParkourSubTerrainCfg(), "gap": ParkourGapTerrainCfg()},
    )
    fresh = ParkourTerrainGenerator(cfg, device="cpu")
    cached = ParkourTerrainGenerator(cfg, device="cpu")
    np.testing.assert_allclose(fresh.terrain_mesh.vertices, cached.terrain_mesh.vertices, atol=1e-6)
    np.testing.assert_array_equal(fresh.terrain_mesh.faces, cached.terrain_mesh.faces)
    assert fresh.task_regions[0, 0].layout.family == "box"
    assert fresh.task_regions[0, 1].layout.family == "gap"
    for row in range(2):
        record = fresh.task_regions[row, 1]
        assert row / 2 <= record.layout.difficulty < (row + 1) / 2
        np.testing.assert_allclose(record.tile_to_world[:3, 3], [-10 + row * 10, 0, 0])
        assert record.layout.canonical_id == cached.task_regions[row, 1].layout.canonical_id


def test_narrow_valid_tile_still_has_positive_wall_solids():
    cfg = ParkourGapTerrainCfg(size=(5.8, 6.1))
    meshes, _ = cfg.function(1.0, cfg)
    assert all(mesh.is_watertight and mesh.volume > 0 and np.all(mesh.area_faces > 0) for mesh in meshes)
