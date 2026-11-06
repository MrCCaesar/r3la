"""Side-slope analytic surface, triangle-interior error and exact matched mirror."""

import numpy as np
import pytest
import trimesh

from r3la.labs.terrains.layouts import build_terrain_layout
from r3la.labs.terrains.trimesh.mesh_terrains_cfg import ParkourSideSlopeTerrainCfg


def top_triangles(mesh, bounds):
    tri = mesh.triangles
    inside = ((tri[..., :2] >= bounds[0] - 1e-9) & (tri[..., :2] <= bounds[1] + 1e-9)).all(axis=(1, 2))
    return tri[inside & (mesh.face_normals[:, 2] > 0.5)]


@pytest.mark.parametrize("difficulty", [0.0, 1.0])
@pytest.mark.parametrize("mirror_sign", [1, -1])
def test_side_slope_direct_joins_and_far_landing(difficulty, mirror_sign):
    cfg = ParkourSideSlopeTerrainCfg(mirror_sign=mirror_sign)
    layout = build_terrain_layout(difficulty, cfg)
    meshes, origin = cfg.function(difficulty, cfg)
    assert all(m.is_watertight and m.is_winding_consistent and m.volume > 0 for m in meshes)
    mesh = trimesh.util.concatenate(meshes)
    starts = [
        [2.9, 4.4, 2],
        [3.001, 4.4, 2],
        [3.25, 4.4, 2],
        [3.5, 4.4, 2],
        [4.5, 5.6, 2],
        [4.75, 5.6, 2],
        [4.999, 5.6, 2],
        [6, 5.6, 2],
    ]
    hits, ray, _ = mesh.ray.intersects_location(starts, [[0, 0, -1]] * len(starts), multiple_hits=False)
    t = mirror_sign * np.tan(np.deg2rad(20 * difficulty))
    np.testing.assert_allclose(hits[np.argsort(ray), 2], [0, abs(t) - 0.6 * t, abs(t) - 0.6 * t, abs(t) - 0.6 * t, abs(t) + 0.6 * t, abs(t) + 0.6 * t, abs(t) + 0.6 * t, 0], atol=1e-7)
    np.testing.assert_allclose(layout.geometry.break_x, [3, 5])
    np.testing.assert_allclose(layout.support_surface.xy_bounds, [[5, 4], [7, 6]])
    np.testing.assert_allclose(layout.completion_xy, [[5.15, 4.15], [6.85, 5.85]])
    np.testing.assert_allclose(origin, [6, 5, 0])
    assert [g.x for g in layout.gates] == [3, 5]


@pytest.mark.parametrize("mirror_sign", [1, -1])
def test_rotated_ramp_is_exactly_planar(mirror_sign):
    cfg = ParkourSideSlopeTerrainCfg(mirror_sign=mirror_sign)
    layout = build_terrain_layout(1.0, cfg)
    mesh = trimesh.util.concatenate(cfg.function(1.0, cfg)[0])
    triangles = top_triangles(mesh, layout.geometry.xy_bounds)
    assert len(triangles) == 2
    # A rotated ordinary ramp is exactly planar, including triangle interiors.
    midpoint = (triangles + np.roll(triangles, -1, axis=1)) / 2
    expected = layout.geometry.height_at(midpoint[..., 0], midpoint[..., 1])
    np.testing.assert_allclose(midpoint[..., 2], expected, atol=1e-12)


def test_mirror_reflects_surface_heights():
    cfg = ParkourSideSlopeTerrainCfg()
    mirror = cfg.replace(mirror_sign=-1)
    a, b = build_terrain_layout(1.0, cfg), build_terrain_layout(1.0, mirror)
    assert a.canonical_id == b.canonical_id
    ma = trimesh.util.concatenate(cfg.function(1.0, cfg)[0])
    mb = trimesh.util.concatenate(mirror.function(1.0, mirror)[0])
    # Interior points off grid edges catch the wrong reflected grid diagonal.
    rng = np.random.default_rng(43)
    points = np.column_stack((rng.uniform(3, 5, 40), rng.uniform(4, 6, 40), np.full(40, 2.0)))
    hits_a, ids_a, _ = ma.ray.intersects_location(points, [[0, 0, -1]] * len(points), multiple_hits=False)
    points[:, 1] = 10 - points[:, 1]
    hits_b, ids_b, _ = mb.ray.intersects_location(points, [[0, 0, -1]] * len(points), multiple_hits=False)
    np.testing.assert_allclose(hits_a[np.argsort(ids_a), 2], hits_b[np.argsort(ids_b), 2], atol=1e-9)


def test_asymmetric_mirror_transforms_profile_spawn_and_landing():
    cfg = ParkourSideSlopeTerrainCfg(size=(7.0, 6.0))
    canonical = build_terrain_layout(1.0, cfg)
    mirror = build_terrain_layout(1.0, cfg.replace(mirror_sign=-1))
    assert canonical.canonical_id == mirror.canonical_id
    np.testing.assert_allclose(mirror.spawn_pos, [2, 1, 0])
    np.testing.assert_allclose(mirror.legal_xy, [[1, 0], [7, 2]])
    np.testing.assert_allclose(mirror.support_surface.xy_bounds, [[5, 0], [7, 2]])
    np.testing.assert_allclose(mirror.completion_xy, [[5.15, 0.15], [6.85, 1.85]])
    np.testing.assert_allclose(mirror.gates[0].y_bounds, [0, 2])
    meshes, _ = cfg.replace(mirror_sign=-1).function(1.0, cfg.replace(mirror_sign=-1))
    assert all(m.is_watertight and m.volume > 0 and np.all(m.area_faces > 0) for m in meshes)
    assert mirror.geometry.height_at(3.25, 0.4) == pytest.approx(canonical.geometry.height_at(3.25, 5.6))


def test_invalid_profile_and_landing_are_rejected():
    from dataclasses import replace

    from r3la.labs.terrains.layouts import SideSlopeGeometry

    with pytest.raises(ValueError, match="side_slope terrain"):
        build_terrain_layout(1.0, ParkourSideSlopeTerrainCfg(size=(6.9, 10.0)))
    with pytest.raises(ValueError, match="side_slope terrain"):
        SideSlopeGeometry(np.array([3.0, 4.0, 3.5, 5.0]), np.array([[3, 4], [5, 6]]), 5.0, 0.3)
    layout = build_terrain_layout(1.0, ParkourSideSlopeTerrainCfg())
    with pytest.raises(ValueError, match="side_slope terrain"):
        replace(layout, geometry=replace(layout.geometry, slope=0.0))
    with pytest.raises(ValueError, match="side_slope terrain"):
        replace(layout, support_surface=replace(layout.support_surface, offset=-0.5))


def test_slope_cache_and_mirror_preserve_canonical_sample(tmp_path):
    from isaaclab.terrains import TerrainGeneratorCfg

    from r3la.labs.terrains.terrain_generator import ParkourTerrainGenerator

    cfg = TerrainGeneratorCfg(
        class_type=ParkourTerrainGenerator,
        seed=47,
        size=(10.0, 10.0),
        num_rows=2,
        num_cols=1,
        border_width=0,
        curriculum=True,
        use_cache=True,
        cache_dir=str(tmp_path),
        color_scheme="none",
        sub_terrains={"side_slope": ParkourSideSlopeTerrainCfg()},
    )
    a = ParkourTerrainGenerator(cfg, device="cpu")
    cfg.sub_terrains["side_slope"].mirror_sign = -1
    b = ParkourTerrainGenerator(cfg, device="cpu")
    cached = ParkourTerrainGenerator(cfg, device="cpu")
    np.testing.assert_allclose(b.terrain_mesh.vertices, cached.terrain_mesh.vertices, atol=1e-6)
    np.testing.assert_array_equal(b.terrain_mesh.faces, cached.terrain_mesh.faces)
    for row in range(2):
        la, lb = a.task_regions[row, 0].layout, b.task_regions[row, 0].layout
        assert la.difficulty == lb.difficulty and la.canonical_id == lb.canonical_id
        assert lb.geometry.slope == -la.geometry.slope
        assert row / 2 <= la.difficulty < (row + 1) / 2


def test_layout_rejects_wrong_extent_or_gate_spans():
    from dataclasses import replace

    from r3la.labs.terrains.layouts import Gate

    layout = build_terrain_layout(1.0, ParkourSideSlopeTerrainCfg())
    with pytest.raises(ValueError, match="side_slope terrain"):
        replace(layout, geometry=replace(layout.geometry, break_x=np.array([3.0, 3.25, 4.75, 5.0])))
    with pytest.raises(ValueError, match="side_slope terrain"):
        replace(layout, gates=(Gate(3.0, np.array([4.2, 5.8])), layout.gates[1]))


@pytest.mark.parametrize("difficulty", [0.0, 0.5, 1.0])
@pytest.mark.parametrize("mirror_sign", [1, -1])
def test_low_edge_is_ground_aligned_and_entire_top_above_ground(difficulty, mirror_sign):
    cfg = ParkourSideSlopeTerrainCfg(mirror_sign=mirror_sign)
    layout = build_terrain_layout(difficulty, cfg)
    mesh = cfg.function(difficulty, cfg)[0][0]
    top = top_triangles(mesh, layout.geometry.xy_bounds)
    assert top[..., 2].min() == pytest.approx(0, abs=1e-12)
    assert top[..., 2].max() == pytest.approx(2 * np.tan(np.deg2rad(20 * difficulty)))
    low_y = 4 if mirror_sign == 1 else 6
    np.testing.assert_allclose(layout.geometry.height_at([3, 4, 5], low_y), 0, atol=1e-12)
    # Only the closed solid's base is below ground; no walkable slope is buried.
    assert all(m.is_watertight and m.volume > 0 for m in cfg.function(difficulty, cfg)[0])
