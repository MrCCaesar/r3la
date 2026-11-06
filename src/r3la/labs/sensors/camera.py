"""Newton depth camera with row-isolated held metric samples."""

import math

import torch

from isaaclab.sensors.camera import Camera
from isaaclab_newton.renderers import NewtonWarpRendererCfg

from .sample import _HeldSample


class HeldDepthCamera(_HeldSample, Camera):
    """Copy inside the native scalar capture hook before renderer aliases change."""

    def __init__(self, cfg):
        if not isinstance(cfg.renderer_cfg, NewtonWarpRendererCfg):
            raise ValueError("HeldDepthCamera currently requires the approved Newton Warp renderer")
        if "distance_to_image_plane" not in cfg.data_types or cfg.spawn is None:
            raise ValueError(
                "HeldDepthCamera requires spawned distance_to_image_plane for its depth sample; "
                "additional native data_types are allowed. Use CameraCfg for a camera without depth."
            )
        # Native Camera validates additional outputs against the renderer capabilities.
        # They remain available through data.output; only metric depth enters sample.
        near, far = cfg.spawn.clipping_range
        if not (0 < near < far < float("inf")):
            raise ValueError("HeldDepthCamera clipping range must be finite, positive and ordered")
        if not math.isfinite(cfg.update_period) or cfg.update_period <= 0:
            raise ValueError("HeldDepthCamera update_period must be finite and positive")
        calibration = (cfg.spawn.focal_length, cfg.spawn.horizontal_aperture, cfg.spawn.vertical_aperture)
        if (
            not all(x is not None and math.isfinite(x) and x > 0 for x in calibration)
            or not all(math.isfinite(x) for x in (*cfg.offset.pos, *cfg.offset.rot))
            or not math.isclose(sum(x * x for x in cfg.offset.rot), 1.0, abs_tol=1e-6)
            or cfg.height <= 0
            or cfg.width <= 0
        ):
            raise ValueError("HeldDepthCamera requires finite positive calibration and a unit offset quaternion")
        super().__init__(cfg)

    def _initialize_impl(self):
        super()._initialize_impl()
        depth = self._data.output["distance_to_image_plane"].torch
        if depth.shape != (self._num_envs, self.cfg.height, self.cfg.width, 1) or depth.dtype != torch.float32:
            raise RuntimeError("Unsupported native image-plane depth shape or dtype")
        self._initialize_sample(depth.shape)

    def _update_buffers_impl(self, env_mask):
        super()._update_buffers_impl(env_mask)
        depth = self._data.output["distance_to_image_plane"].torch
        near, far = self.cfg.spawn.clipping_range
        valid = torch.isfinite(depth) & (depth >= near) & (depth <= far)
        self._store_sample(env_mask, torch.where(valid, depth, 0.0), valid)
