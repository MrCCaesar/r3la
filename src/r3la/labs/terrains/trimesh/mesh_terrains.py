"""Directed parkour meshes with the native (meshes, origin) return contract."""

import numpy as np
import trimesh

from ..layouts import (
    BoxGeometry,
    GapGeometry,
    RoughGridGeometry,
    SideSlopeGeometry,
    StairGeometry,
    build_terrain_layout,
)


def box_terrain(difficulty, cfg):
    layout = build_terrain_layout(difficulty, cfg)
    if not isinstance(layout.geometry, BoxGeometry):
        raise ValueError("box terrain: mesh function/config family mismatch")
    sx, sy = layout.tile_size
    ground = trimesh.creation.box(extents=(sx, sy, 0.1))
    ground.apply_translation((sx / 2, sy / 2, -0.05))
    height = layout.geometry.height
    bounds = layout.geometry.top_bounds
    center = bounds.mean(axis=0)
    width = bounds[1] - bounds[0]
    box = trimesh.creation.box(extents=(*width, height))
    box.apply_translation((*center, height / 2))
    return [ground, box], np.array([*center, height], dtype=np.float64)


def gap_terrain(difficulty, cfg):
    """A finite-depth ditch with solid approach, floor, walls and far-side ground."""
    layout = build_terrain_layout(difficulty, cfg)
    sx, sy = layout.tile_size
    geometry = layout.geometry
    if not isinstance(geometry, GapGeometry):
        raise ValueError("gap terrain: mesh function/config family mismatch")
    (near, left), (far, right) = geometry.ditch_bounds
    bottom = -geometry.depth - 0.1
    meshes = []
    # These closed solids meet at the trench edges; no ground slab covers the floor.
    for x0, x1, y0, y1, top in (
        (0.0, near, 0.0, sy, 0.0),
        (far, sx, 0.0, sy, 0.0),
        (near, far, 0.0, left, 0.0),
        (near, far, right, sy, 0.0),
        (near, far, left, right, -geometry.depth),
    ):
        mesh = trimesh.creation.box(extents=(x1 - x0, y1 - y0, top - bottom))
        mesh.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (top + bottom) / 2))
        meshes.append(mesh)
    origin_xy = geometry.landing_bounds.mean(axis=0)
    return meshes, np.array([*origin_xy, 0.0], dtype=np.float64)


def stairs_terrain(difficulty, cfg):
    """Single +X stair flight with native count/residual platform semantics."""
    layout = build_terrain_layout(difficulty, cfg)
    geometry = layout.geometry
    if layout.family != "stairs" or not isinstance(geometry, StairGeometry):
        raise ValueError("stairs terrain: mesh function/config family mismatch")
    sx, sy = layout.tile_size
    ground = trimesh.creation.box(extents=(sx, sy, 0.1))
    ground.apply_translation((sx / 2, sy / 2, -0.05))
    meshes = [ground]
    # Each disjoint longitudinal solid owns one tread; no opposite-side flight.
    for bounds, plane in zip(geometry.tread_bounds, geometry.tread_planes, strict=True):
        height = -plane[3]
        mesh = trimesh.creation.box(extents=(*(bounds[1] - bounds[0]), height + 0.1))
        mesh.apply_translation((*bounds.mean(axis=0), (height - 0.1) / 2))
        meshes.append(mesh)
    platform = geometry.platform_bounds
    height = geometry.platform_height
    mesh = trimesh.creation.box(extents=(*(platform[1] - platform[0]), height + 0.1))
    mesh.apply_translation((*platform.mean(axis=0), (height - 0.1) / 2))
    meshes.append(mesh)
    return meshes, np.array([*platform.mean(axis=0), height], dtype=np.float64)


def _plane_prism(bounds, plane, bottom):
    """Closed rectangular-XY prism with a planar top and horizontal bottom."""
    (x0, y0), (x1, y1) = bounds
    xy = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    top = -(xy @ plane[:2] + plane[3]) / plane[2]
    if not np.isfinite(top).all() or np.min(top) <= bottom:
        raise ValueError("tilted_stairs terrain: invalid prism top/bottom")
    vertices = np.vstack((np.column_stack((xy, np.full(4, bottom))), np.column_stack((xy, top))))
    faces = [
        [0, 2, 1],
        [0, 3, 2],
        [4, 5, 6],
        [4, 6, 7],
        [0, 1, 5],
        [0, 5, 4],
        [1, 2, 6],
        [1, 6, 5],
        [2, 3, 7],
        [2, 7, 6],
        [3, 0, 4],
        [3, 4, 7],
    ]
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)


def tilted_stairs_terrain(difficulty, cfg):
    """Preserve sheared tread tops, horizontal entrance/platform and negative low sides."""
    layout = build_terrain_layout(difficulty, cfg)
    geometry = layout.geometry
    if layout.family != "tilted_stairs" or not isinstance(geometry, StairGeometry):
        raise ValueError("tilted_stairs terrain: mesh function/config family mismatch")
    sx, sy = layout.tile_size
    minimum = 0.0
    for bounds, plane in zip(geometry.tread_bounds, geometry.tread_planes, strict=True):
        corners = np.array(
            [
                [bounds[0, 0], bounds[0, 1]],
                [bounds[0, 0], bounds[1, 1]],
                [bounds[1, 0], bounds[0, 1]],
                [bounds[1, 0], bounds[1, 1]],
            ]
        )
        minimum = min(minimum, float(np.min(-(corners @ plane[:2] + plane[3]) / plane[2])))
    bottom = minimum - 0.1
    flat = np.array([0.0, 0.0, 1.0, 0.0])
    meshes = []

    def add_flat(x0, x1, y0, y1):
        # Empty outer strips at tile edges are absent, not zero-volume meshes.
        if x1 > x0 and y1 > y0:
            meshes.append(_plane_prism(np.array([[x0, y0], [x1, y1]]), flat, bottom))

    add_flat(0.0, geometry.tread_bounds[0, 0, 0], 0.0, sy)
    for bounds, plane in zip(geometry.tread_bounds, geometry.tread_planes, strict=True):
        meshes.append(_plane_prism(bounds, plane, bottom))
        add_flat(bounds[0, 0], bounds[1, 0], 0.0, bounds[0, 1])
        add_flat(bounds[0, 0], bounds[1, 0], bounds[1, 1], sy)
    platform = geometry.platform_bounds
    platform_plane = np.array([0.0, 0.0, 1.0, -geometry.platform_height])
    meshes.append(_plane_prism(platform, platform_plane, bottom))
    add_flat(platform[0, 0], platform[1, 0], 0.0, platform[0, 1])
    add_flat(platform[0, 0], platform[1, 0], platform[1, 1], sy)
    add_flat(platform[1, 0], sx, 0.0, sy)
    return meshes, np.array([*platform.mean(axis=0), geometry.platform_height], dtype=np.float64)


def side_slope_terrain(difficulty, cfg):
    """Transverse planar ramp with direct, unblended joins to flat ground."""
    layout = build_terrain_layout(difficulty, cfg)
    geometry = layout.geometry
    if layout.family != "side_slope" or not isinstance(geometry, SideSlopeGeometry):
        raise ValueError("side_slope terrain: mesh function/config family mismatch")
    # A longitudinal ramp rotated 90 degrees: one plane, no X transition ramps.
    y0, y1 = geometry.xy_bounds[:, 1]
    center_height = geometry.height_at(geometry.break_x.mean(), geometry.center_y)
    plane = np.array([0.0, -geometry.slope, 1.0, geometry.center_y * geometry.slope - center_height])
    bottom = min(0.0, *(geometry.height_at(geometry.break_x[0], np.array([y0, y1])))) - 0.1
    meshes = [_plane_prism(geometry.xy_bounds, plane, bottom)]
    flat = np.array([0.0, 0.0, 1.0, 0.0])
    sx, sy = layout.tile_size
    start, end = geometry.break_x[[0, -1]]
    # Surround the ramp with flat ground; its lowest edge lies at z=0.
    for bounds in (
        np.array([[0.0, 0.0], [start, sy]]),
        np.array([[end, 0.0], [sx, sy]]),
        np.array([[start, 0.0], [end, y0]]),
        np.array([[start, y1], [end, sy]]),
    ):
        if np.all(bounds[1] > bounds[0]):
            meshes.append(_plane_prism(bounds, flat, bottom))
    origin = layout.support_surface.xy_bounds.mean(axis=0)
    return meshes, np.array([*origin, 0.0], dtype=np.float64)


def rough_grid_terrain(difficulty, cfg):
    """Exact positive-height2x2m box patch; no center platform or random device state."""
    layout = build_terrain_layout(difficulty, cfg)
    geometry = layout.geometry
    if layout.family != "rough_grid" or not isinstance(geometry, RoughGridGeometry):
        raise ValueError("rough_grid terrain: mesh function/config family mismatch")
    sx, sy = layout.tile_size
    ground = trimesh.creation.box(extents=(sx, sy, 0.1))
    ground.apply_translation((sx / 2, sy / 2, -0.05))
    meshes = [ground]
    # Local adaptation of native box-grid construction. Edge-derived extents tile
    # exactly, including the zero-residual-border case rejected by native grid code.
    for ix, (x0, x1) in enumerate(zip(geometry.x_edges[:-1], geometry.x_edges[1:], strict=True)):
        for iy, (y0, y1) in enumerate(zip(geometry.y_edges[:-1], geometry.y_edges[1:], strict=True)):
            height = geometry.heights[ix, iy]
            mesh = trimesh.creation.box(extents=(x1 - x0, y1 - y0, height + 0.1))
            mesh.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (height - 0.1) / 2))
            meshes.append(mesh)
    center = layout.support_surface.xy_bounds.mean(axis=0)
    return meshes, np.array([*center, 0.0], dtype=np.float64)
