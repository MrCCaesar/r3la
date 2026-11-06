"""Deterministic local task geometry, independent of mesh placement and simulation."""

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

# Bound count-dependent mesh/metadata allocations before materializing arrays.
_MAX_STAIR_TREADS = 1000


def _array(value):
    result = np.array(value, dtype=np.float64)
    result.flags.writeable = False
    return result


@dataclass(frozen=True)
class Gate:
    x: float
    y_bounds: np.ndarray

    def __post_init__(self):
        object.__setattr__(self, "y_bounds", _array(self.y_bounds))


@dataclass(frozen=True)
class PlaneRegion:
    xy_bounds: np.ndarray
    normal: np.ndarray
    offset: float

    def __post_init__(self):
        object.__setattr__(self, "xy_bounds", _array(self.xy_bounds))
        object.__setattr__(self, "normal", _array(self.normal))


@dataclass(frozen=True)
class BoxGeometry:
    height: float
    top_bounds: np.ndarray

    def __post_init__(self):
        object.__setattr__(self, "top_bounds", _array(self.top_bounds))
        if (
            self.top_bounds.shape != (2, 2)
            or not np.isfinite(self.top_bounds).all()
            or np.any(self.top_bounds[1] <= self.top_bounds[0])
        ):
            raise ValueError("box terrain: invalid top bounds")
        if not np.isfinite(self.height) or self.height <= 0:
            raise ValueError("box terrain: invalid height")


@dataclass(frozen=True)
class GapGeometry:
    width: float
    depth: float
    ditch_bounds: np.ndarray
    landing_bounds: np.ndarray

    def __post_init__(self):
        if not np.isfinite([self.width, self.depth]).all() or self.width <= 0 or self.depth <= 0:
            raise ValueError("gap terrain: invalid width/depth")
        for name in ("ditch_bounds", "landing_bounds"):
            bounds = _array(getattr(self, name))
            if bounds.shape != (2, 2) or not np.isfinite(bounds).all() or np.any(bounds[1] <= bounds[0]):
                raise ValueError(f"gap terrain: invalid {name}")
            object.__setattr__(self, name, bounds)
        if (
            not np.isclose(self.ditch_bounds[1, 0] - self.ditch_bounds[0, 0], self.width)
            or not np.isclose(self.landing_bounds[0, 0], self.ditch_bounds[1, 0])
            or not np.allclose(self.ditch_bounds[:, 1], self.landing_bounds[:, 1])
        ):
            raise ValueError("gap terrain: ditch and landing geometry disagree")


@dataclass(frozen=True)
class StairGeometry:
    count: int
    rise: float
    tread_depth: float
    holes: bool
    tread_bounds: np.ndarray
    tread_planes: np.ndarray
    platform_bounds: np.ndarray
    platform_height: float

    def __post_init__(self):
        if (
            not isinstance(self.count, int)
            or not 1 <= self.count <= _MAX_STAIR_TREADS
            or not np.isfinite([self.rise, self.tread_depth, self.platform_height]).all()
            or self.rise <= 0
            or self.tread_depth <= 0
            or not isinstance(self.holes, bool)
        ):
            raise ValueError("stairs terrain: invalid count/rise/tread depth")
        for name, shape in (
            ("tread_bounds", (self.count, 2, 2)),
            ("tread_planes", (self.count, 4)),
            ("platform_bounds", (2, 2)),
        ):
            value = _array(getattr(self, name))
            if value.shape != shape or not np.isfinite(value).all():
                raise ValueError(f"stairs terrain: invalid {name}")
            object.__setattr__(self, name, value)
        if (
            np.any(self.tread_bounds[:, 1] <= self.tread_bounds[:, 0])
            or np.any(self.platform_bounds[1] <= self.platform_bounds[0])
            or not np.allclose(np.linalg.norm(self.tread_planes[:, :3], axis=1), 1)
            or not np.isclose(self.platform_height, (self.count + 1) * self.rise)
        ):
            raise ValueError("stairs terrain: invalid bounds/planes/platform rise")


@dataclass(frozen=True)
class SideSlopeGeometry:
    break_x: np.ndarray
    xy_bounds: np.ndarray
    center_y: float
    slope: float

    def __post_init__(self):
        object.__setattr__(self, "break_x", _array(self.break_x))
        object.__setattr__(self, "xy_bounds", _array(self.xy_bounds))
        if (
            self.break_x.shape != (2,)
            or not np.isfinite(self.break_x).all()
            or np.any(np.diff(self.break_x) <= 0)
            or self.xy_bounds.shape != (2, 2)
            or not np.isfinite(self.xy_bounds).all()
            or np.any(self.xy_bounds[1] <= self.xy_bounds[0])
            or not np.isfinite([self.center_y, self.slope]).all()
            or not self.xy_bounds[0, 1] <= self.center_y <= self.xy_bounds[1, 1]
            or not np.allclose(self.xy_bounds[:, 0], self.break_x[[0, -1]])
        ):
            raise ValueError("side_slope terrain: invalid analytic surface")

    def height_at(self, x, y):
        """Analytic surface, with zero height outside its longitudinal section."""
        envelope = (np.asarray(x) >= self.break_x[0]) & (np.asarray(x) <= self.break_x[-1])
        low_y = self.xy_bounds[0, 1] if self.slope >= 0 else self.xy_bounds[1, 1]
        return (np.asarray(y) - low_y) * self.slope * envelope


@lru_cache(maxsize=256)
def _rough_grid_sample(identity: str, maximum: float) -> np.ndarray:
    """One immutable generation-time sample per identity (height arrays <=200KiB).

    The layout and native mesh hooks may ask for the same definition separately.
    Reuse this sample rather than advancing another RNG stream. On a fresh process
    the local, identity-seeded generator reconstructs exactly the same sample.
    """
    rng = np.random.Generator(np.random.PCG64(int(identity, 16)))
    return _array(rng.uniform(0.0, maximum, (10, 10)))


@dataclass(frozen=True)
class RoughGridGeometry:
    """Cell edges in metres; height matrix indexed [X cell, Y cell]."""

    x_edges: np.ndarray
    y_edges: np.ndarray
    heights: np.ndarray
    maximum_height: float

    def __post_init__(self):
        for name, shape in (("x_edges", (11,)), ("y_edges", (11,)), ("heights", (10, 10))):
            value = _array(getattr(self, name))
            if value.shape != shape or not np.isfinite(value).all():
                raise ValueError(f"rough_grid terrain: invalid {name}")
            object.__setattr__(self, name, value)
        if (
            not np.isfinite(self.maximum_height)
            or self.maximum_height <= 0
            or not np.allclose(np.diff(self.x_edges), 0.2)
            or not np.allclose(np.diff(self.y_edges), 0.2)
            or np.any(self.heights < 0)
            or np.any(self.heights > self.maximum_height)
        ):
            raise ValueError("rough_grid terrain: invalid cell spacing/heights")


@dataclass(frozen=True)
class TerrainLayout:
    schema_version: int
    family: str
    seed: int
    canonical_id: str
    difficulty: float
    mirror_sign: int
    tile_size: np.ndarray
    spawn_pos: np.ndarray
    spawn_yaw: float
    legal_xy: np.ndarray
    gates: tuple[Gate, ...]
    completion_xy: np.ndarray
    support_surface: PlaneRegion
    geometry: BoxGeometry | GapGeometry | StairGeometry | SideSlopeGeometry | RoughGridGeometry

    def __post_init__(self):
        context = f"{self.family} terrain"
        object.__setattr__(self, "gates", tuple(self.gates))
        shapes = {
            "tile_size": (2,),
            "spawn_pos": (3,),
            "legal_xy": (2, 2),
            "completion_xy": (2, 2),
        }
        for name, shape in shapes.items():
            value = np.asarray(getattr(self, name))
            if value.shape != shape or not np.isfinite(value).all():
                raise ValueError(f"{context}: invalid {name}")
            object.__setattr__(self, name, _array(value))
        if self.schema_version != 1 or self.family not in (
            "box",
            "gap",
            "stairs",
            "tilted_stairs",
            "side_slope",
            "rough_grid",
        ):
            raise ValueError(f"{context}: invalid schema/family")
        if not np.isfinite([self.difficulty, self.spawn_yaw]).all() or not 0 <= self.difficulty <= 1:
            raise ValueError(f"{context}: invalid difficulty/yaw")
        if self.mirror_sign not in (-1, 1) or not self.canonical_id or np.any(self.tile_size <= 0):
            raise ValueError(f"{context}: invalid identity/dimensions")
        for bounds in (self.legal_xy, self.completion_xy, self.support_surface.xy_bounds):
            if np.asarray(bounds).shape != (2, 2) or not np.isfinite(bounds).all() or np.any(bounds[1] <= bounds[0]):
                raise ValueError(f"{context}: invalid region bounds")
            if np.any(bounds[0] < 0) or np.any(bounds[1] > self.tile_size):
                raise ValueError(f"{context}: region outside tile")
        if np.any(
            np.minimum(self.legal_xy[1], self.completion_xy[1]) <= np.maximum(self.legal_xy[0], self.completion_xy[0])
        ):
            raise ValueError(f"{context}: empty completion/corridor intersection")
        normal = self.support_surface.normal
        if (
            np.asarray(normal).shape != (3,)
            or not np.isfinite(normal).all()
            or not np.isclose(np.linalg.norm(normal), 1)
        ):
            raise ValueError(f"{context}: invalid support normal")
        if self.family == "box":
            if not isinstance(self.geometry, BoxGeometry):
                raise ValueError("box terrain: invalid geometry payload")
            if (
                not np.allclose(self.geometry.top_bounds, self.support_surface.xy_bounds)
                or not np.allclose(normal, [0, 0, 1])
                or not np.isclose(self.support_surface.offset, -self.geometry.height)
            ):
                raise ValueError("box terrain: geometry and support surface disagree")
        if self.family == "gap":
            if (
                not isinstance(self.geometry, GapGeometry)
                or not np.allclose(self.geometry.landing_bounds, self.support_surface.xy_bounds)
                or not np.allclose(normal, [0, 0, 1])
                or not np.isclose(self.support_surface.offset, 0)
            ):
                raise ValueError("gap terrain: geometry and support surface disagree")
            if len(self.gates) != 2 or not np.allclose([g.x for g in self.gates], self.geometry.ditch_bounds[:, 0]):
                raise ValueError("gap terrain: gates and ditch disagree")
        if self.family in ("stairs", "tilted_stairs"):
            if (
                not isinstance(self.geometry, StairGeometry)
                or not np.allclose(self.geometry.platform_bounds, self.support_surface.xy_bounds)
                or not np.allclose(normal, [0, 0, 1])
                or not np.isclose(self.support_surface.offset, -self.geometry.platform_height)
            ):
                raise ValueError("stairs terrain: geometry and support surface disagree")
            bounds = self.geometry.tread_bounds
            count = self.geometry.count
            expected_planes = np.zeros((count, 4))
            slope = (
                self.mirror_sign * np.tan(np.deg2rad(15 * self.difficulty)) if self.family == "tilted_stairs" else 0.0
            )
            expected_planes[:, 1] = -slope
            expected_planes[:, 2] = 1
            expected_planes[:, 3] = -np.arange(1, count + 1) * self.geometry.rise + self.spawn_pos[1] * slope
            expected_planes /= np.hypot(1.0, slope)
            expected_x = bounds[0, 0, 0] + np.arange(count) * self.geometry.tread_depth
            if (
                not np.allclose(self.geometry.tread_planes, expected_planes)
                or not np.allclose(bounds[:, 0, 0], expected_x)
                or not np.allclose(bounds[:, 1, 0], expected_x + self.geometry.tread_depth)
                or not np.isclose(bounds[-1, 1, 0], self.geometry.platform_bounds[0, 0])
            ):
                raise ValueError("stairs terrain: tread geometry and planes disagree")
            if (
                np.any(bounds[:, 0] < 0)
                or np.any(bounds[:, 1] > self.tile_size)
                or len(self.gates) != 2
                or not np.allclose([g.x for g in self.gates], [bounds[0, 0, 0], self.geometry.platform_bounds[0, 0]])
            ):
                raise ValueError("stairs terrain: invalid tread bounds/gates")
        if self.family == "side_slope":
            geometry = self.geometry
            if (
                not isinstance(geometry, SideSlopeGeometry)
                or not np.isclose(geometry.center_y, self.spawn_pos[1])
                or not np.isclose(geometry.slope, self.mirror_sign * np.tan(np.deg2rad(20 * self.difficulty)))
                or len(self.gates) != 2
                or not np.allclose([g.x for g in self.gates], geometry.break_x[[0, -1]])
                or not np.allclose(normal, [0, 0, 1])
                or not np.isclose(self.support_surface.offset, 0)
                or np.any(geometry.xy_bounds[0] < 0)
                or np.any(geometry.xy_bounds[1] > self.tile_size)
            ):
                raise ValueError("side_slope terrain: geometry/task metadata disagree")
            if (
                not np.allclose(geometry.break_x, [3.0, 5.0])
                or not np.allclose(geometry.xy_bounds[:, 1], self.spawn_pos[1] + np.array([-1.0, 1.0]))
                or not np.allclose(self.legal_xy, [[1.0, geometry.xy_bounds[0, 1]], [7.0, geometry.xy_bounds[1, 1]]])
                or any(not np.allclose(g.y_bounds, geometry.xy_bounds[:, 1]) for g in self.gates)
            ):
                raise ValueError("side_slope terrain: invalid slope/corridor/gate contract")
            landing = np.array(
                [
                    [geometry.break_x[-1], geometry.xy_bounds[0, 1]],
                    [geometry.break_x[-1] + 2.0, geometry.xy_bounds[1, 1]],
                ]
            )
            if not np.allclose(self.support_surface.xy_bounds, landing):
                raise ValueError("side_slope terrain: invalid landing support")
        if self.family == "rough_grid":
            geometry = self.geometry
            if (
                not isinstance(geometry, RoughGridGeometry)
                or not np.allclose(geometry.x_edges, np.linspace(3, 5, 11))
                or not np.allclose(geometry.y_edges, np.linspace(4, 6, 11))
                or not np.isclose(geometry.maximum_height, 0.02 + 0.18 * self.difficulty)
                or self.mirror_sign != 1
                or not np.allclose(self.spawn_pos, [2, 5, 0])
                or not np.allclose(self.legal_xy, [[1, 4], [7, 6]])
                or len(self.gates) != 2
                or not np.allclose([g.x for g in self.gates], [3, 5])
                or any(not np.allclose(g.y_bounds, [4, 6]) for g in self.gates)
                or not np.allclose(self.support_surface.xy_bounds, [[5, 4], [7, 6]])
                or not np.allclose(self.completion_xy, [[5.15, 4.15], [6.85, 5.85]])
                or not np.allclose(normal, [0, 0, 1])
                or not np.isclose(self.support_surface.offset, 0)
            ):
                raise ValueError("rough_grid terrain: geometry/task metadata disagree")
        if not np.isfinite(self.support_surface.offset):
            raise ValueError(f"{context}: invalid support plane")
        previous_x = self.legal_xy[0, 0]
        if not self.gates:
            raise ValueError(f"{context}: missing gates")
        for gate in self.gates:
            if not np.isfinite(gate.x) or gate.x <= previous_x or gate.x > self.legal_xy[1, 0]:
                raise ValueError(f"{context}: inconsistent gate order")
            span = np.asarray(gate.y_bounds)
            if span.shape != (2,) or not np.isfinite(span).all() or span[1] <= span[0]:
                raise ValueError(f"{context}: invalid gate span")
            if span[0] < self.legal_xy[0, 1] or span[1] > self.legal_xy[1, 1]:
                raise ValueError(f"{context}: gate span outside corridor")
            previous_x = gate.x
        if not np.all((self.spawn_pos[:2] >= self.legal_xy[0]) & (self.spawn_pos[:2] <= self.legal_xy[1])):
            raise ValueError(f"{context}: spawn outside approach")

    def validate_spawn_footprint(self, radius: float, jitter: float = 0.2) -> None:
        """Prove a conservative whole-robot disc stays on the flat approach."""
        if not np.isfinite([radius, jitter]).all() or radius <= 0 or jitter < 0:
            raise ValueError(f"{self.family} terrain: invalid spawn footprint")
        lower = self.legal_xy[0]
        upper = np.array([self.gates[0].x, self.legal_xy[1, 1]])
        extent = radius + jitter
        if np.any(self.spawn_pos[:2] - extent < lower) or np.any(self.spawn_pos[:2] + extent > upper):
            raise ValueError(f"{self.family} terrain: full spawn footprint/jitter exceeds approach")


@dataclass(frozen=True)
class PlacedTerrainLayout:
    layout: TerrainLayout
    level: int
    column: int
    tile_to_world: np.ndarray

    def __post_init__(self):
        transform = np.asarray(self.tile_to_world)
        if transform.shape != (4, 4) or not np.isfinite(transform).all():
            raise ValueError(f"{self.layout.family} terrain: invalid placement transform")
        rotation = transform[:3, :3]
        if (
            not np.allclose(rotation.T @ rotation, np.eye(3))
            or not np.isclose(np.linalg.det(rotation), 1)
            or not np.allclose(transform[3], [0, 0, 0, 1])
        ):
            raise ValueError(f"{self.layout.family} terrain: placement must be rigid")
        if self.level < 0 or self.column < 0:
            raise ValueError(f"{self.layout.family} terrain: negative placement index")
        object.__setattr__(self, "tile_to_world", _array(transform))


def build_terrain_layout(difficulty: float, cfg) -> TerrainLayout:
    """Build the implemented parkour layouts; reject unsupported families until implemented."""
    context = f"{cfg.family} terrain"
    if cfg.family not in ("box", "gap", "stairs", "tilted_stairs", "side_slope", "rough_grid"):
        raise ValueError(f"{context}: family not implemented")
    if not np.isfinite(difficulty) or not 0 <= difficulty <= 1:
        raise ValueError(f"{context}: difficulty must be finite and in [0,1]")
    size = np.asarray(cfg.size, dtype=float)
    if size.shape != (2,) or not np.isfinite(size).all() or np.any(size < (4.5, 6.0)):
        raise ValueError(f"{context}: tile must contain the approach and obstacle")
    if (
        cfg.schema_version != 1
        or cfg.mirror_sign not in (-1, 1)
        or (cfg.family not in ("tilted_stairs", "side_slope") and cfg.mirror_sign != 1)
    ):
        raise ValueError(f"{context}: unsupported schema or mirror")
    seed = 0 if cfg.seed is None else int(cfg.seed)
    identity_fields = [1, cfg.family, seed, float(difficulty), size.tolist()]
    if hasattr(cfg, "geometry_revision"):
        identity_fields.append(cfg.geometry_revision)
    identity = hashlib.sha256(json.dumps(identity_fields).encode()).hexdigest()
    if cfg.family == "rough_grid":
        if size[0] < 7:
            raise ValueError("rough_grid terrain: tile must contain obstacle and far landing")
        maximum = 0.02 + 0.18 * float(difficulty)
        return TerrainLayout(
            schema_version=1,
            family="rough_grid",
            seed=seed,
            canonical_id=identity,
            difficulty=float(difficulty),
            mirror_sign=1,
            tile_size=_array(size),
            spawn_pos=_array([2, 5, 0]),
            spawn_yaw=0.0,
            legal_xy=_array([[1, 4], [7, 6]]),
            gates=(Gate(3.0, _array([4, 6])), Gate(5.0, _array([4, 6]))),
            completion_xy=_array([[5.15, 4.15], [6.85, 5.85]]),
            support_surface=PlaneRegion(_array([[5, 4], [7, 6]]), _array([0, 0, 1]), 0.0),
            geometry=RoughGridGeometry(
                x_edges=np.linspace(3, 5, 11),
                y_edges=np.linspace(4, 6, 11),
                heights=_rough_grid_sample(identity, maximum),
                maximum_height=maximum,
            ),
        )
    if cfg.family == "side_slope":
        if size[0] < 7:
            raise ValueError("side_slope terrain: tile must contain obstacle and far landing")
        center_y = 5.0 if cfg.mirror_sign == 1 else size[1] - 5.0
        y0, y1 = center_y - 1.0, center_y + 1.0
        bounds = _array([[3.0, y0], [5.0, y1]])
        landing = _array([[5.0, y0], [7.0, y1]])
        return TerrainLayout(
            schema_version=1,
            family="side_slope",
            seed=seed,
            canonical_id=identity,
            difficulty=float(difficulty),
            mirror_sign=cfg.mirror_sign,
            tile_size=_array(size),
            spawn_pos=_array([2.0, center_y, 0.0]),
            spawn_yaw=0.0,
            legal_xy=_array([[1.0, y0], [7.0, y1]]),
            gates=(Gate(3.0, _array([y0, y1])), Gate(5.0, _array([y0, y1]))),
            completion_xy=_array([landing[0] + 0.15, landing[1] - 0.15]),
            support_surface=PlaneRegion(landing, _array([0, 0, 1]), 0.0),
            geometry=SideSlopeGeometry(
                break_x=_array([3.0, 5.0]),
                xy_bounds=bounds,
                center_y=center_y,
                slope=cfg.mirror_sign * np.tan(np.deg2rad(20 * difficulty)),
            ),
        )
    if cfg.family == "gap":
        width = 0.2 + 0.6 * difficulty
        far = 3 + width
        if size[1] <= 6:
            raise ValueError("gap terrain: tile must leave positive thickness for both sidewalls")
        if size[0] < far + 2:
            raise ValueError("gap terrain: tile must contain the far landing")
        landing = _array([[far, 4], [far + 2, 6]])
        return TerrainLayout(
            schema_version=1,
            family="gap",
            seed=seed,
            canonical_id=identity,
            difficulty=float(difficulty),
            mirror_sign=1,
            tile_size=_array(size),
            spawn_pos=_array([2, 5, 0]),
            spawn_yaw=0.0,
            legal_xy=_array([[1, 4], [far + 2, 6]]),
            gates=(Gate(3.0, _array([4, 6])), Gate(far, _array([4, 6]))),
            completion_xy=_array([landing[0] + 0.15, landing[1] - 0.15]),
            support_surface=PlaneRegion(landing, _array([0, 0, 1]), 0.0),
            geometry=GapGeometry(
                width=width, depth=1.0, ditch_bounds=_array([[3, 4], [far, 6]]), landing_bounds=landing
            ),
        )
    if cfg.family in ("stairs", "tilted_stairs"):
        try:
            t, p, b = cfg.step_width, cfg.platform_width, cfg.border_width
            low, high = cfg.step_height_range
            holes = cfg.holes
        except (AttributeError, TypeError, ValueError):
            raise ValueError("stairs terrain: invalid stair configuration") from None
        try:
            t, p, b, low, high = map(float, (t, p, b, low, high))
        except (ValueError, TypeError, OverflowError):
            raise ValueError("stairs terrain: invalid numeric parameters") from None
        if (
            not np.isfinite([t, p, b, low, high]).all()
            or t <= 0
            or p <= 0
            or b < 0
            or low <= 0
            or high < low
            or not isinstance(holes, bool)
        ):
            raise ValueError("stairs terrain: invalid step/platform/border/height parameters")
        sx, sy = size - np.array([3.0, 0.0])
        # Match native floor-division exactly; validate before int conversion/allocation.
        raw_count = min((float(sx) - 2 * b - p) // (2 * t) + 1, (float(sy) - 2 * b - p) // (2 * t) + 1)
        if not np.isfinite(raw_count) or not 1 <= raw_count <= _MAX_STAIR_TREADS:
            raise ValueError(f"stairs terrain: count exceeds bounded generation range [1,{_MAX_STAIR_TREADS}]")
        count = int(raw_count)
        px, py = np.array([sx, sy]) - 2 * b - 2 * count * t
        if count <= 0 or min(px, py) <= 0.3:
            raise ValueError("stairs terrain: empty stair flight or platform inset")
        py = p if holes else py
        rise = low + (high - low) * difficulty
        platform_x = 3 + count * t
        platform = _array([[platform_x, 5 - py / 2], [platform_x + px, 5 + py / 2]])
        indices = np.arange(count)
        spans = np.full(count, p) if holes else sy - 2 * b - 2 * indices * t
        tread_bounds = np.stack(
            (
                np.column_stack((3 + indices * t, 5 - spans / 2)),
                np.column_stack((3 + (indices + 1) * t, 5 + spans / 2)),
            ),
            axis=1,
        )
        heights = (indices + 1) * rise
        slope = np.tan(np.deg2rad(15 * difficulty)) if cfg.family == "tilted_stairs" else 0.0
        planes = np.column_stack((np.zeros(count), np.full(count, -slope), np.ones(count), -heights + 5 * slope))
        planes /= np.hypot(1.0, slope)
        legal = _array([[1, 4], [platform[1, 0], 6]])
        spawn_y = 5.0
        if cfg.mirror_sign == -1:
            # Reflect canonical geometry and metadata together, before placement.
            def reflected_bounds(bounds):
                result = bounds.copy()
                result[..., 0, 1] = size[1] - bounds[..., 1, 1]
                result[..., 1, 1] = size[1] - bounds[..., 0, 1]
                return _array(result)

            tread_bounds = reflected_bounds(tread_bounds)
            platform = reflected_bounds(platform)
            legal = reflected_bounds(legal)
            spawn_y = size[1] - spawn_y
            planes[:, 1] *= -1
            planes[:, 3] -= planes[:, 1] * size[1]
        top = (count + 1) * rise
        stair_identity = hashlib.sha256(json.dumps([identity, t, p, b, low, high, holes]).encode()).hexdigest()
        return TerrainLayout(
            schema_version=1,
            family=cfg.family,
            seed=seed,
            canonical_id=stair_identity,
            difficulty=float(difficulty),
            mirror_sign=cfg.mirror_sign,
            tile_size=_array(size),
            spawn_pos=_array([2, spawn_y, 0]),
            spawn_yaw=0.0,
            legal_xy=legal,
            gates=(
                Gate(3.0, _array([max(legal[0, 1], tread_bounds[0, 0, 1]), min(legal[1, 1], tread_bounds[0, 1, 1])])),
                Gate(platform_x, _array([max(legal[0, 1], platform[0, 1]), min(legal[1, 1], platform[1, 1])])),
            ),
            completion_xy=_array([platform[0] + 0.15, platform[1] - 0.15]),
            support_surface=PlaneRegion(platform, _array([0, 0, 1]), -top),
            geometry=StairGeometry(
                count=count,
                rise=rise,
                tread_depth=t,
                holes=holes,
                tread_bounds=tread_bounds,
                tread_planes=planes,
                platform_bounds=platform,
                platform_height=top,
            ),
        )
    height = 0.1 + 0.5 * difficulty
    bounds = _array([[3, 4.25], [4.5, 5.75]])
    return TerrainLayout(
        schema_version=1,
        family="box",
        seed=seed,
        canonical_id=identity,
        difficulty=float(difficulty),
        mirror_sign=1,
        tile_size=_array(size),
        spawn_pos=_array([2, 5, 0]),
        spawn_yaw=0.0,
        legal_xy=_array([[1, 4], [4.5, 6]]),
        gates=(Gate(3.0, _array([4.25, 5.75])),),
        completion_xy=_array([[3.15, 4.4], [4.35, 5.6]]),
        support_surface=PlaneRegion(bounds, _array([0, 0, 1]), -height),
        geometry=BoxGeometry(height=height, top_bounds=bounds),
    )
