"""Native configurations for implemented parkour terrain families."""

from isaaclab.terrains import SubTerrainBaseCfg
from isaaclab.utils import configclass


@configclass
class ParkourSubTerrainCfg(SubTerrainBaseCfg):
    function: str = "{DIR}.mesh_terrains:box_terrain"
    family: str = "box"
    seed: int = 0
    schema_version: int = 1
    mirror_sign: int = 1


@configclass
class ParkourGapTerrainCfg(ParkourSubTerrainCfg):
    """Approved gap: width interpolates .2–.8 m and depth is 1 m."""

    function: str = "{DIR}.mesh_terrains:gap_terrain"
    family: str = "gap"


@configclass
class ParkourStairsTerrainCfg(ParkourSubTerrainCfg):
    """Single flight; holes=True makes tread and platform Y spans platform_width."""

    function: str = "{DIR}.mesh_terrains:stairs_terrain"
    family: str = "stairs"
    geometry_revision: int = 2  # Invalidate native caches for the equal-width platform.
    step_width: float = 0.30
    step_height_range: tuple[float, float] = (0.05, 0.23)
    platform_width: float = 1.5
    border_width: float = 0.0
    holes: bool = False


@configclass
class ParkourTiltedStairsTerrainCfg(ParkourStairsTerrainCfg):
    """Shear only treads by15*d degrees; mirror_sign=-1 reflects the canonical sample."""

    function: str = "{DIR}.mesh_terrains:tilted_stairs_terrain"
    family: str = "tilted_stairs"


@configclass
class ParkourSideSlopeTerrainCfg(ParkourSubTerrainCfg):
    """Approved0–20 degree transverse slope; reflect using mirror_sign=-1."""

    function: str = "{DIR}.mesh_terrains:side_slope_terrain"
    family: str = "side_slope"
    geometry_revision: int = 3  # Ground-aligned low edge; invalidate centered-plane caches.


@configclass
class ParkourRoughGridTerrainCfg(ParkourSubTerrainCfg):
    """Exact10x10 box cells with heights U[0,.02+.18*d], fixed for generated geometry."""

    function: str = "{DIR}.mesh_terrains:rough_grid_terrain"
    family: str = "rough_grid"
