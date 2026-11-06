"""Approved directed staircase count, residual platform and collision surfaces."""

import numpy as np
import pytest
import trimesh

from r3la.labs.terrains.layouts import build_terrain_layout
from r3la.labs.terrains.trimesh.mesh_terrains_cfg import ParkourStairsTerrainCfg


@pytest.mark.parametrize(("difficulty", "rise", "top"), [(0.0, 0.05, 0.55), (1.0, 0.23, 2.53)])
@pytest.mark.parametrize("holes", [False, True])
def test_native_count_residual_platform_and_single_flight(difficulty, rise, top, holes):
    cfg = ParkourStairsTerrainCfg(holes=holes)
    layout = build_terrain_layout(difficulty, cfg)
    geometry = layout.geometry
    assert geometry.count == 10
    assert geometry.rise == pytest.approx(rise)
    np.testing.assert_allclose(geometry.platform_bounds, [[6, 4.25], [7, 5.75]] if holes else [[6, 3], [7, 7]])
    np.testing.assert_allclose(layout.completion_xy, [[6.15, 4.4], [6.85, 5.6]] if holes else [[6.15, 3.15], [6.85, 6.85]])
    assert geometry.platform_height == pytest.approx(top)
    assert [g.x for g in layout.gates] == pytest.approx([3, 6])
    np.testing.assert_allclose(layout.gates[0].y_bounds, [4.25, 5.75] if holes else [4, 6])
    np.testing.assert_allclose(layout.gates[1].y_bounds, [4.25, 5.75] if holes else [4, 6])
    meshes, origin = cfg.function(difficulty, cfg)
    assert all(m.is_watertight and m.volume > 0 and np.all(m.area_faces > 0) for m in meshes)
    np.testing.assert_allclose(origin, [6.5, 5, top])
    mesh = trimesh.util.concatenate(meshes)
    starts = [[3.15, 5, 4], [5.85, 5, 4], [6.5, 5, 4], [3.15, 5.9, 4], [7.5, 5, 4]]
    hits, rays, _ = mesh.ray.intersects_location(starts, [[0, 0, -1]] * len(starts), multiple_hits=False)
    hits = hits[np.argsort(rays)]
    np.testing.assert_allclose(hits[:, 2], [rise, 10 * rise, top, 0 if holes else rise, 0], atol=1e-7)


def test_parameter_changes_recompute_actual_regions_and_cache_identity():
    default = build_terrain_layout(1, ParkourStairsTerrainCfg())
    wider = build_terrain_layout(1, ParkourStairsTerrainCfg(size=(11, 10)))
    finer = build_terrain_layout(1, ParkourStairsTerrainCfg(step_width=0.25))
    assert wider.geometry.count == 11
    np.testing.assert_allclose(wider.geometry.platform_bounds, [[6.3, 3.3], [7.7, 6.7]])
    assert wider.gates[1].x == pytest.approx(6.3)
    np.testing.assert_allclose(wider.completion_xy, [[6.45, 3.45], [7.55, 6.55]])
    assert finer.geometry.count == 12
    assert len({default.canonical_id, wider.canonical_id, finer.canonical_id}) == 3
    holes = build_terrain_layout(1, ParkourStairsTerrainCfg(holes=True))
    assert holes.canonical_id != default.canonical_id


@pytest.mark.parametrize(
    "params",
    [
        {"step_width": 0},
        {"step_width": float("nan")},
        {"platform_width": 0.1},
        {"border_width": -1},
        {"border_width": 10},
        {"platform_width": 20},
        {"step_height_range": (0, 0.23)},
        {"step_height_range": (0.23, 0.05)},
    ],
)
def test_invalid_stair_geometry_is_rejected(params):
    with pytest.raises(ValueError, match="stairs terrain"):
        build_terrain_layout(0.5, ParkourStairsTerrainCfg(**params))


@pytest.mark.parametrize("holes", [False, True])
def test_stair_cache_preserves_tread_layout_and_sampled_difficulty(tmp_path, holes):
    from isaaclab.terrains import TerrainGeneratorCfg

    from r3la.labs.terrains.terrain_generator import ParkourTerrainGenerator

    cfg = TerrainGeneratorCfg(
        class_type=ParkourTerrainGenerator,
        seed=23,
        size=(10.0, 10.0),
        num_rows=2,
        num_cols=1,
        border_width=0,
        curriculum=True,
        use_cache=True,
        cache_dir=str(tmp_path),
        color_scheme="none",
        sub_terrains={"stairs": ParkourStairsTerrainCfg(holes=holes)},
    )
    first = ParkourTerrainGenerator(cfg, device="cpu")
    cached = ParkourTerrainGenerator(cfg, device="cpu")
    np.testing.assert_allclose(first.terrain_mesh.vertices, cached.terrain_mesh.vertices, atol=1e-6)
    np.testing.assert_array_equal(first.terrain_mesh.faces, cached.terrain_mesh.faces)
    for row in range(2):
        a, b = first.task_regions[row, 0], cached.task_regions[row, 0]
        assert a.layout.canonical_id == b.layout.canonical_id
        assert row / 2 <= a.layout.difficulty < (row + 1) / 2
        np.testing.assert_allclose(a.layout.geometry.tread_planes, b.layout.geometry.tread_planes)
        np.testing.assert_allclose(a.tile_to_world[:3, 3], [-10 + row * 10, -5, 0])


@pytest.mark.parametrize("width", [1e-309, 1e-9, "bad"])
def test_stair_count_errors_are_bounded_and_contextual(width):
    with pytest.raises(ValueError, match="stairs terrain"):
        build_terrain_layout(0.5, ParkourStairsTerrainCfg(step_width=width))


def test_ordinary_stair_metadata_rejects_nonhorizontal_or_wrong_height_planes():
    from dataclasses import replace

    layout = build_terrain_layout(1, ParkourStairsTerrainCfg())
    for plane in ([1.0, 0.0, 0.0, -0.23], [0.0, 0.0, 1.0, -1.0]):
        planes = layout.geometry.tread_planes.copy()
        planes[0] = plane
        geometry = replace(layout.geometry, tread_planes=planes)
        with pytest.raises(ValueError, match="stairs terrain"):
            replace(layout, geometry=geometry)


@pytest.mark.parametrize("family", ["stairs", "tilted_stairs"])
def test_holes_platform_and_treads_share_y_edges_and_collision(family):
    from r3la.labs.terrains.trimesh.mesh_terrains_cfg import ParkourTiltedStairsTerrainCfg

    cls = ParkourStairsTerrainCfg if family == "stairs" else ParkourTiltedStairsTerrainCfg
    cfg = cls(holes=True)
    layout = build_terrain_layout(1.0, cfg)
    geometry = layout.geometry
    for tread in geometry.tread_bounds:
        np.testing.assert_allclose(tread[:, 1], geometry.platform_bounds[:, 1])
    mesh = trimesh.util.concatenate(cfg.function(1.0, cfg)[0])
    starts = [[6.5, 4.24, 4], [6.5, 4.26, 4], [6.5, 5.74, 4], [6.5, 5.76, 4]]
    hits, ids, _ = mesh.ray.intersects_location(starts, [[0, 0, -1]] * 4, multiple_hits=False)
    np.testing.assert_allclose(hits[np.argsort(ids), 2], [0, 2.53, 2.53, 0], atol=1e-7)
