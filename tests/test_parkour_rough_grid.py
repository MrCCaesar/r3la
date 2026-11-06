"""Deterministic positive box-grid geometry, collision tops and native cache parity."""

import numpy as np
import pytest
import trimesh

from r3la.labs.terrains.layouts import build_terrain_layout
from r3la.labs.terrains.trimesh.mesh_terrains_cfg import ParkourRoughGridTerrainCfg


@pytest.mark.parametrize(("difficulty", "maximum"), [(0.0, 0.02), (1.0, 0.20)])
def test_all_cell_tops_match_one_canonical_positive_height_sample(difficulty, maximum):
    cfg = ParkourRoughGridTerrainCfg(seed=19)
    layout = build_terrain_layout(difficulty, cfg)
    geometry = layout.geometry
    assert geometry.heights.shape == (10, 10)
    assert geometry.heights.dtype == np.float64
    assert not geometry.heights.flags.writeable
    assert np.all((geometry.heights >= 0) & (geometry.heights <= maximum))
    assert np.ptp(geometry.heights) > maximum * 0.7
    np.testing.assert_allclose(geometry.x_edges, np.linspace(3, 5, 11))
    np.testing.assert_allclose(geometry.y_edges, np.linspace(4, 6, 11))
    np.testing.assert_allclose(layout.support_surface.xy_bounds, [[5, 4], [7, 6]])
    np.testing.assert_allclose(layout.completion_xy, [[5.15, 4.15], [6.85, 5.85]])
    assert [g.x for g in layout.gates] == [3, 5]
    meshes, origin = cfg.function(difficulty, cfg)
    assert len(meshes) == 101  # Ground and exactly100 cells; no extra central platform.
    assert all(m.is_watertight and m.volume > 0 and np.all(m.area_faces > 0) for m in meshes)
    np.testing.assert_allclose(origin, [6, 5, 0])
    mesh = trimesh.util.concatenate(meshes)
    xx, yy = np.meshgrid(np.linspace(3.1, 4.9, 10), np.linspace(4.1, 5.9, 10), indexing="ij")
    starts = np.column_stack((xx.ravel(), yy.ravel(), np.ones(100)))
    hits, ray, _ = mesh.ray.intersects_location(starts, [[0, 0, -1]] * 100, multiple_hits=False)
    np.testing.assert_allclose(hits[np.argsort(ray), 2].reshape(10, 10), geometry.heights, atol=1e-7)
    # A rising adjacent pair must have a real vertical collision face, with no deliberate gap.
    ix, iy = np.argwhere(geometry.heights[1:] > geometry.heights[:-1])[0]
    level = (geometry.heights[ix, iy] + geometry.heights[ix + 1, iy]) / 2
    start = [[xx[ix, iy], yy[ix, iy], level]]
    hits, _, _ = mesh.ray.intersects_location(start, [[1, 0, 0]], multiple_hits=False)
    assert hits[0, 0] == pytest.approx(geometry.x_edges[ix + 1])


def test_seed_reproduction_is_independent_of_global_rng_and_attempts():
    before = np.random.get_state()
    cfg = ParkourRoughGridTerrainCfg(seed=991)
    a = build_terrain_layout(0.123, cfg)
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
    b = build_terrain_layout(0.123, cfg)
    np.testing.assert_array_equal(a.geometry.heights, b.geometry.heights)
    assert a.canonical_id == b.canonical_id
    c = build_terrain_layout(0.123, cfg.replace(seed=992))
    assert c.canonical_id != a.canonical_id
    assert not np.array_equal(c.geometry.heights, a.geometry.heights)
    # Difficulty is part of sample identity, not just a post-hoc amplitude rescaling.
    d = build_terrain_layout(0.5, cfg)
    assert not np.allclose(d.geometry.heights / 0.11, a.geometry.heights / (0.02 + 0.18 * 0.123))


def test_native_cache_hits_and_uncached_geometry_share_height_matrix(tmp_path):
    from isaaclab.terrains import TerrainGeneratorCfg

    from r3la.labs.terrains.terrain_generator import ParkourTerrainGenerator

    cfg = TerrainGeneratorCfg(
        class_type=ParkourTerrainGenerator,
        seed=53,
        size=(10.0, 10.0),
        num_rows=2,
        num_cols=1,
        border_width=0,
        curriculum=True,
        use_cache=True,
        cache_dir=str(tmp_path),
        color_scheme="none",
        sub_terrains={"rough_grid": ParkourRoughGridTerrainCfg()},
    )
    fresh = ParkourTerrainGenerator(cfg, device="cpu")
    cached = ParkourTerrainGenerator(cfg, device="cpu")
    cfg.use_cache = False
    uncached = ParkourTerrainGenerator(cfg, device="cpu")
    for other in (cached, uncached):
        np.testing.assert_allclose(fresh.terrain_mesh.vertices, other.terrain_mesh.vertices, atol=1e-6)
        np.testing.assert_array_equal(fresh.terrain_mesh.faces, other.terrain_mesh.faces)
        for row in range(2):
            a, b = fresh.task_regions[row, 0].layout, other.task_regions[row, 0].layout
            assert a.canonical_id == b.canonical_id and a.difficulty == b.difficulty
            np.testing.assert_array_equal(a.geometry.heights, b.geometry.heights)
            assert row / 2 <= a.difficulty < (row + 1) / 2


def test_invalid_grid_payload_or_unapproved_mirror_is_rejected():
    from dataclasses import replace

    layout = build_terrain_layout(1.0, ParkourRoughGridTerrainCfg())
    for value in (float("nan"), -0.001, 0.201):
        heights = layout.geometry.heights.copy()
        heights[0, 0] = value
        with pytest.raises(ValueError, match="rough_grid terrain"):
            replace(layout.geometry, heights=heights)
    with pytest.raises(ValueError, match="rough_grid terrain"):
        replace(layout.geometry, heights=np.zeros((9, 10)))
    with pytest.raises(ValueError, match="rough_grid terrain"):
        build_terrain_layout(1.0, ParkourRoughGridTerrainCfg(mirror_sign=-1))
    with pytest.raises(ValueError, match="rough_grid terrain"):
        build_terrain_layout(1.0, ParkourRoughGridTerrainCfg(size=(6.9, 10)))
