"""Native Newton ray queries at foot position with base yaw, without a new clock."""

import math

import torch
import warp as wp

from isaaclab.cloner.cloner_cfg import expand_env_regex_ns
from isaaclab.sensors import patterns
from isaaclab_newton.sensors.ray_caster.newton_raycast_sensor import NewtonRaycastSensor

from .sample import _HeldSample


@wp.kernel(enable_backward=False)
def _compose_heading(
    indices: wp.array(dtype=wp.int32),
    shape_body: wp.array(dtype=wp.int32),
    shape_transform: wp.array(dtype=wp.transform),
    body_q: wp.array(dtype=wp.transform),
    poses: wp.array(dtype=wp.transform),
    quats: wp.array(dtype=wp.quat),
):
    row = wp.tid()
    site = indices[row]
    body = shape_body[site]
    heading_pose = shape_transform[site]
    if body >= 0:
        heading_pose = wp.transform_multiply(body_q[body], heading_pose)
    heading = wp.transform_get_rotation(heading_pose)
    poses[row] = wp.transform(wp.transform_get_translation(poses[row]), heading)
    quats[row] = heading


class BaseYawHeightScanner(_HeldSample, NewtonRaycastSensor):
    """Register both frames before model finalization and compose persistent poses."""

    def __init__(self, cfg):
        if not math.isfinite(cfg.update_period) or cfg.update_period <= 0:
            raise ValueError("BaseYawHeightScanner update_period must be finite and positive")
        grid = cfg.pattern_cfg
        if (
            not isinstance(grid, patterns.GridPatternCfg)
            or grid.ordering != "xy"
            or grid.direction != (0.0, 0.0, -1.0)
            or not all(math.isfinite(x) and x > 0 for x in (*grid.size, grid.resolution))
        ):
            raise ValueError("BaseYawHeightScanner requires a finite positive xy grid of world-down rays")
        if (
            cfg.ray_alignment != "yaw"
            or not cfg.global_world_only
            or cfg.max_distance != 5.0
            or cfg.offset.pos != (0.0, 0.0, 2.0)
            or cfg.offset.rot != (0.0, 0.0, 0.0, 1.0)
            or any(cfg.drift_range)
            or any(any(v) for v in cfg.ray_cast_drift_range.values())
        ):
            raise ValueError("BaseYawHeightScanner requires yaw, global terrain, 2 m launch, 5 m reach and no drift")
        super().__init__(cfg)
        self._heading_site_label = self._backend_manager.register_site(
            expand_env_regex_ns(cfg.heading_prim_path), wp.transform()
        )

    def _initialize_impl(self):
        super()._initialize_impl()
        site_map = self._backend_manager.get_site_index_map()
        if self._heading_site_label not in site_map:
            raise ValueError(f"Base heading site not found for '{self.cfg.heading_prim_path}'")
        global_index, per_world = site_map[self._heading_site_label]
        indices = [global_index] * self._num_envs if per_world is None else [i for sites in per_world for i in sites]
        if len(indices) != self._num_envs:
            raise ValueError("Base heading must resolve exactly one pose site per environment")
        self._heading_site_indices = wp.array(indices, dtype=wp.int32, device=self._device)
        self._initialize_sample((self._num_envs, self.num_rays))

    def get_world_poses(self, indices=None):
        # Native query graphs retain these buffers. No per-capture pose allocation.
        super().get_world_poses()
        wp.launch(
            _compose_heading,
            dim=self._num_envs,
            inputs=[
                self._heading_site_indices,
                self.backend.model.shape_body,
                self.backend.model.shape_transform,
                self.backend.state_0.body_q,
            ],
            outputs=[self._newton_pose_w, self._newton_quat_w.warp],
            device=self._device,
        )
        if indices is not None:
            raise ValueError("BaseYawHeightScanner pose tracking supports full native pose batches only")
        return self._newton_pos_w, self._newton_quat_w

    def _update_buffers_impl(self, env_mask):
        super()._update_buffers_impl(env_mask)
        hits = self._data.ray_hits_w.torch
        heights = self._data.pos_w.torch[:, 2:3] - hits[..., 2]
        valid = torch.isfinite(hits).all(dim=-1) & torch.isfinite(heights)
        self._store_sample(env_mask, torch.where(valid, heights, 0.0), valid)
