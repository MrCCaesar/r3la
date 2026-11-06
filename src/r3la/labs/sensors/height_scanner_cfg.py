"""Reference-body position and independent base-yaw Newton height scanner."""

from dataclasses import MISSING

from isaaclab.sensors import RayCasterCfg, patterns
from isaaclab.utils import configclass
from isaaclab_newton.sensors.ray_caster.newton_raycast_sensor_cfg import NewtonRaycastSensorCfg


@configclass
class BaseYawHeightScannerCfg(NewtonRaycastSensorCfg):
    """Heights use reference Z; launch starts 2 m above it and reaches 5 m."""

    class_type: str = "{DIR}.height_scanner:BaseYawHeightScanner"
    heading_prim_path: str = MISSING
    update_period: float = 0.1
    offset = RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 2.0))
    ray_alignment: str = "yaw"
    pattern_cfg = patterns.GridPatternCfg(resolution=0.05, size=(0.2, 0.2), ordering="xy")
    max_distance: float = 5.0
    global_world_only: bool = True
    debug_vis: bool = False
