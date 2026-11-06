"""Approved 87 degree, metric image-plane depth camera calibration."""

import math

from isaaclab.sensors import CameraCfg
from isaaclab.sim import PinholeCameraCfg
from isaaclab.utils import configclass
from isaaclab_newton.renderers import NewtonWarpRendererCfg


@configclass
class HeldDepthCameraCfg(CameraCfg):
    """320x240 depth at 10 Hz; native offset quaternion is xyzw.

    Keep distance_to_image_plane for the held training sample. Additional native
    outputs (e.g. rgb, normals) are optional debug views in camera.data.output,
    with native buffer lifetime; clone them when retaining frames.
    """

    class_type: str = "{DIR}.camera:HeldDepthCamera"
    update_period: float = 0.1
    update_latest_camera_pose: bool = True
    height: int = 240
    width: int = 320
    data_types: list[str] = ["distance_to_image_plane"]
    # R columns: optical X -> -base Y, optical Y -> -base Z, optical Z -> base X.
    offset = CameraCfg.OffsetCfg(pos=(0.35, 0.0, 0.05), rot=(0.5, -0.5, 0.5, -0.5), convention="ros")
    spawn = PinholeCameraCfg(
        focal_length=24.0,
        horizontal_aperture=48.0 * math.tan(math.radians(43.5)),
        vertical_aperture=36.0 * math.tan(math.radians(43.5)),
        clipping_range=(0.1, 5.0),
    )
    renderer_cfg = NewtonWarpRendererCfg()
