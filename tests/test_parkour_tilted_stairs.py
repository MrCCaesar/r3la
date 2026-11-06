"""Sheared tread planes, horizontal joins and matched reflection contracts."""

import numpy as np
import pytest
import trimesh

from r3la.labs.terrains.layouts import build_terrain_layout
from r3la.labs.terrains.trimesh.mesh_terrains_cfg import ParkourTiltedStairsTerrainCfg


@pytest.mark.parametrize("difficulty", [0.0, 1.0])
@pytest.mark.parametrize("holes", [False, True])
@pytest.mark.parametrize("mirror_sign", [1, -1])
def test_tread_planes_and_horizontal_entrance_platform(difficulty, holes, mirror_sign):
    cfg = ParkourTiltedStairsTerrainCfg(holes=holes, mirror_sign=mirror_sign)
    layout = build_terrain_layout(difficulty, cfg)
    meshes, origin = cfg.function(difficulty, cfg)
    mesh = trimesh.util.concatenate(meshes)
    assert all(m.is_watertight and m.is_winding_consistent and m.volume > 0 for m in meshes)
    rise = 0.05 + 0.18 * difficulty
    slope = mirror_sign * np.tan(np.deg2rad(15 * difficulty))
    y = 4.3 if holes else 4.05
    starts = [[2.9, y, 5], [3.15, y, 5], [5.85, 10 - y, 5], [6.1, y, 5], [6.9, 10 - y, 5]]
    hits, rays, _ = mesh.ray.intersects_location(starts, [[0, 0, -1]] * len(starts), multiple_hits=False)
    hits = hits[np.argsort(rays)]
    np.testing.assert_allclose(
        hits[:, 2], [0, rise + (y - 5) * slope, 10 * rise + (5 - y) * slope, 11 * rise, 11 * rise], atol=1e-7
    )
    np.testing.assert_allclose(origin, [6.5, 5, 11 * rise])
    np.testing.assert_allclose(layout.support_surface.normal, [0, 0, 1])
    np.testing.assert_allclose(layout.completion_xy, [[6.15, 4.4], [6.85, 5.6]] if holes else [[6.15, 3.15], [6.85, 6.85]])
    # Test the generated triangles against the documented planes at interior points.
    for point in hits[[1, 2]]:
        k = 0 if point[0] < 4 else 9
        plane = layout.geometry.tread_planes[k]
        assert np.dot(plane[:3], point) + plane[3] == pytest.approx(0, abs=1e-7)


def test_low_side_and_sign_changing_entrance_platform_joins_are_preserved():
    cfg = ParkourTiltedStairsTerrainCfg()
    meshes, _ = cfg.function(1.0, cfg)
    mesh = trimesh.util.concatenate(meshes)
    # Probe both sides of the first and final joins, within the legal route.
    starts = [
        [2.999, 4, 5],
        [3.001, 4, 5],
        [2.999, 6, 5],
        [3.001, 6, 5],
        [5.999, 6, 5],
        [6.001, 6, 5],
        [5.999, 4, 5],
        [6.001, 4, 5],
    ]
    hits, rays, _ = mesh.ray.intersects_location(starts, [[0, 0, -1]] * len(starts), multiple_hits=False)
    z = hits[np.argsort(rays), 2]
    t = np.tan(np.deg2rad(15))
    np.testing.assert_allclose(z, [0, 0.23 - t, 0, 0.23 + t, 2.3 + t, 2.53, 2.3 - t, 2.53], atol=1e-7)
    assert z[1] < 0  # A full flat ground overlay would incorrectly turn this into zero.
    assert z[5] - z[4] < 0  # High-side final join is a downstep, not silently levelled.


@pytest.mark.parametrize("holes", [False, True])
def test_mirror_reuses_canonical_geometry_and_reflects_every_region(holes):
    cfg = ParkourTiltedStairsTerrainCfg(holes=holes)
    mirrored_cfg = cfg.replace(mirror_sign=-1)
    a = build_terrain_layout(1.0, cfg)
    b = build_terrain_layout(1.0, mirrored_cfg)
    assert a.canonical_id == b.canonical_id
    ma = trimesh.util.concatenate(cfg.function(1.0, cfg)[0])
    mb = trimesh.util.concatenate(mirrored_cfg.function(1.0, mirrored_cfg)[0])
    reflected = ma.vertices.copy()
    reflected[:, 1] = 10 - reflected[:, 1]

    def ordered(v):
        return v[np.lexsort(np.round(v, 10).T)]

    np.testing.assert_allclose(ordered(reflected), ordered(mb.vertices), atol=1e-9)
    for name in ("legal_xy", "completion_xy"):
        bounds = getattr(a, name)
        expected = bounds.copy()
        expected[:, 1] = 10 - bounds[::-1, 1]
        np.testing.assert_allclose(getattr(b, name), expected)
    for ga, gb in zip(a.gates, b.gates, strict=True):
        assert ga.x == gb.x
        np.testing.assert_allclose(gb.y_bounds, 10 - ga.y_bounds[::-1])
    np.testing.assert_allclose(b.geometry.tread_planes[:, 1], -a.geometry.tread_planes[:, 1])


def test_reflection_moves_asymmetric_regions_spawn_and_plane_offsets():
    cfg = ParkourTiltedStairsTerrainCfg(size=(10.0, 12.0), holes=True)
    a = build_terrain_layout(1.0, cfg)
    b = build_terrain_layout(1.0, cfg.replace(mirror_sign=-1))
    assert a.canonical_id == b.canonical_id
    np.testing.assert_allclose(a.spawn_pos, [2, 5, 0])
    np.testing.assert_allclose(b.spawn_pos, [2, 7, 0])
    np.testing.assert_allclose(b.legal_xy, [[1, 6], [7, 8]])
    np.testing.assert_allclose(b.support_surface.xy_bounds, [[6, 6.25], [7, 7.75]])
    np.testing.assert_allclose(b.completion_xy, [[6.15, 6.4], [6.85, 7.6]])
    np.testing.assert_allclose(b.gates[0].y_bounds, [6.25, 7.75])
    np.testing.assert_allclose(b.gates[1].y_bounds, [6.25, 7.75])
    point = np.array([3.15, 4.5, 0.23 - 0.5 * np.tan(np.deg2rad(15))])
    reflected = point.copy()
    reflected[1] = 12 - point[1]
    plane = b.geometry.tread_planes[0]
    assert np.dot(plane[:3], reflected) + plane[3] == pytest.approx(0, abs=1e-8)


def test_signed_join_faces_close_without_changing_surface_heights():
    cfg = ParkourTiltedStairsTerrainCfg()
    mesh = trimesh.util.concatenate(cfg.function(1.0, cfg)[0])
    t = np.tan(np.deg2rad(15))
    starts = [
        [3.15, 4, (0.23 - t) / 2],
        [2.9, 6, (0.23 + t) / 2],
        [6.1, 6, (2.3 + t + 2.53) / 2],
        [5.9, 4, (2.3 - t + 2.53) / 2],
    ]
    directions = [[-1, 0, 0], [1, 0, 0], [-1, 0, 0], [1, 0, 0]]
    hits, rays, _ = mesh.ray.intersects_location(starts, directions, multiple_hits=False)
    np.testing.assert_allclose(hits[np.argsort(rays), 0], [3, 3, 6, 6], atol=1e-7)


@pytest.mark.parametrize("holes", [False, True])
def test_mirror_generators_preserve_sample_identity_through_cache(tmp_path, holes):
    from isaaclab.terrains import TerrainGeneratorCfg

    from r3la.labs.terrains.terrain_generator import ParkourTerrainGenerator

    cfg = TerrainGeneratorCfg(
        class_type=ParkourTerrainGenerator,
        seed=31,
        size=(10.0, 10.0),
        num_rows=2,
        num_cols=1,
        border_width=0,
        curriculum=True,
        use_cache=True,
        cache_dir=str(tmp_path),
        color_scheme="none",
        sub_terrains={"tilted_stairs": ParkourTiltedStairsTerrainCfg(holes=holes)},
    )
    a = ParkourTerrainGenerator(cfg, device="cpu")
    cfg.sub_terrains["tilted_stairs"].mirror_sign = -1
    b = ParkourTerrainGenerator(cfg, device="cpu")
    cached = ParkourTerrainGenerator(cfg, device="cpu")
    np.testing.assert_allclose(b.terrain_mesh.vertices, cached.terrain_mesh.vertices, atol=1e-6)
    for row in range(2):
        la, lb = a.task_regions[row, 0].layout, b.task_regions[row, 0].layout
        assert la.difficulty == lb.difficulty
        assert la.canonical_id == lb.canonical_id
        assert lb.mirror_sign == -1
        np.testing.assert_allclose(lb.geometry.tread_planes[:, 1], -la.geometry.tread_planes[:, 1])


def test_tilted_metadata_rejects_incorrect_planes_and_unmatched_reflection():
    from dataclasses import replace

    cfg = ParkourTiltedStairsTerrainCfg()
    layout = build_terrain_layout(1.0, cfg)
    with pytest.raises(ValueError, match="terrain"):
        replace(layout, mirror_sign=-1)
    planes = layout.geometry.tread_planes.copy()
    planes[0] = [0.0, 0.0, 1.0, -0.23]
    with pytest.raises(ValueError, match="terrain"):
        replace(layout, geometry=replace(layout.geometry, tread_planes=planes))
    for sign in (0, 2):
        with pytest.raises(ValueError, match="tilted_stairs terrain"):
            build_terrain_layout(1.0, cfg.replace(mirror_sign=sign))


def test_mesh_functions_reject_cross_family_configuration():
    from r3la.labs.terrains.trimesh.mesh_terrains import stairs_terrain

    with pytest.raises(ValueError, match="mismatch"):
        stairs_terrain(1.0, ParkourTiltedStairsTerrainCfg())
