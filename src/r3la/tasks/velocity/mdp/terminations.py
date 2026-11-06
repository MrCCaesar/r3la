"""Native termination-term owner of passage, landing and pre-reset tracking evidence."""

import math

import torch

from isaaclab.managers import ManagerTermBase
from isaaclab.utils.math import euler_xyz_from_quat, wrap_to_pi


class ParkourAttemptState(ManagerTermBase):
    """A finite landing criterion, not a guarantee of indefinite future stability."""

    def __init__(self, cfg, env):
        super().__init__(cfg, env)
        if not math.isclose(env.step_dt, 0.02, abs_tol=1e-8):
            raise ValueError("ParkourAttemptState requires approved 0.02 s control interval")
        self.sensor = env.scene["contact_forces"]
        self.feet, _ = self.sensor.find_bodies(["FL_foot", "FR_foot", "RL_foot", "RR_foot"], preserve_order=True)
        self.base, _ = self.sensor.find_bodies("base", preserve_order=True)
        if len(self.feet) != 4 or len(self.base) != 1:
            raise ValueError("parkour attempt requires four canonical feet and one base")
        if self.sensor.data.contact_pos_w is None or self.sensor.data.normal_force_matrix_w is None:
            raise ValueError("parkour attempt requires terrain-filtered contact point tracking")
        if self.sensor.data.contact_pos_w.torch.shape[2] != 1:
            raise ValueError("parkour attempt requires exactly one terrain contact filter")
        if self.sensor.data.net_normal_forces_w_history.torch.shape[1] < 4:
            raise ValueError("parkour attempt requires four physics samples of contact history")
        n, device = env.num_envs, env.device
        self.gate_progress = torch.zeros(n, dtype=torch.int64, device=device)
        self._previous_xy = torch.zeros((n, 2), device=device)
        self._window_count = torch.zeros(n, dtype=torch.int64, device=device)
        self._support_history = torch.zeros((n, 10, 4), dtype=torch.bool, device=device)
        self.success = torch.zeros(n, dtype=torch.bool, device=device)
        self.bypass = torch.zeros_like(self.success)
        self.ending = torch.zeros_like(self.success)
        self.duration = torch.zeros(n, device=device)
        self.tracking_integral = torch.zeros(n, device=device)
        self._last_step = env.common_step_counter
        self.reset()

    def _local_position(self, position):
        terrain = self._env.scene.terrain
        transform = terrain.task_tile_to_world[terrain.terrain_levels, terrain.terrain_types]
        return torch.einsum("nji,nj->ni", transform[:, :3, :3], position - transform[:, :3, 3])

    def reset(self, env_ids=None):
        ids = slice(None) if env_ids is None else env_ids
        self.gate_progress[ids] = 0
        self._window_count[ids] = 0
        self._support_history[ids] = False
        self.success[ids] = False
        self.bypass[ids] = False
        self.ending[ids] = False
        self.duration[ids] = 0
        self.tracking_integral[ids] = 0
        pos = self._env.scene["robot"].data.root_pos_w.torch
        self._previous_xy[ids] = self._local_position(pos)[ids, :2]
        return {}

    def __call__(self, env):
        if env.common_step_counter == self._last_step:
            return self.success | self.bypass
        self._last_step = env.common_step_counter
        terrain = env.scene.terrain
        rows, cols = terrain.terrain_levels, terrain.terrain_types
        asset = env.scene["robot"].data
        local = self._local_position(asset.root_pos_w.torch)
        xy = local[:, :2]
        previous = self._previous_xy
        legal = terrain.task_legal_xy[rows, cols]
        self.bypass |= ((xy < legal[:, 0]) | (xy > legal[:, 1])).any(dim=1)
        gates = terrain.task_gates[rows, cols]
        gate_count = terrain.task_gate_count[rows, cols]
        dx = xy[:, 0] - previous[:, 0]
        for k in range(gates.shape[1]):
            gx, ymin, ymax = gates[:, k].unbind(-1)
            active = k < gate_count
            forward = active & (previous[:, 0] < gx) & (xy[:, 0] >= gx)
            backward = active & (previous[:, 0] >= gx) & (xy[:, 0] < gx)
            fraction = (gx - previous[:, 0]) / torch.where(dx != 0, dx, torch.ones_like(dx))
            cross_y = previous[:, 1] + fraction * (xy[:, 1] - previous[:, 1])
            valid = (cross_y >= ymin) & (cross_y <= ymax)
            self.bypass |= forward & ~valid
            self.gate_progress = torch.where(backward, self.gate_progress.clamp(max=k), self.gate_progress)
            self.gate_progress += (forward & valid & (self.gate_progress == k)).to(torch.int64)
        self._previous_xy.copy_(xy)
        completion = terrain.task_completion_xy[rows, cols]
        in_region = ((xy >= completion[:, 0]) & (xy <= completion[:, 1])).all(dim=1)
        roll, pitch, _ = euler_xyz_from_quat(asset.root_quat_w.torch)
        attitude_ok = (wrap_to_pi(roll).abs() < math.pi / 6) & (wrap_to_pi(pitch).abs() < math.pi / 6)
        velocity_ok = asset.root_lin_vel_w.torch[:, 2].abs() <= 0.5
        eligible = in_region & attitude_ok & velocity_ok & (self.gate_progress == gate_count)
        # Contacts are native force-weighted aggregates, not exact mesh face IDs.
        contact = self.sensor.data.contact_pos_w.torch[:, self.feet, 0]
        forces = self.sensor.data.normal_force_matrix_w.torch[:, self.feet, 0, 2]
        transform = terrain.task_tile_to_world[rows, cols]
        contact_local = torch.einsum("nji,nfj->nfi", transform[:, :3, :3], contact - transform[:, None, :3, 3])
        support_xy = terrain.task_support_xy[rows, cols]
        support_plane = terrain.task_support_normal[rows, cols]
        plane_distance = (contact_local * support_plane[:, None]).sum(dim=-1) + terrain.task_support_offset[
            rows, cols, None
        ]
        support = (
            (forces > 1)
            & torch.isfinite(contact).all(dim=-1)
            & (
                (contact_local[..., :2] >= support_xy[:, None, 0]) & (contact_local[..., :2] <= support_xy[:, None, 1])
            ).all(dim=-1)
            & (plane_distance.abs() <= 0.03)
        )
        self._support_history = torch.roll(self._support_history, shifts=-1, dims=1)
        self._support_history[:, -1] = support
        self._support_history[~eligible] = False
        self._window_count = torch.where(eligible, (self._window_count + 1).clamp(max=10), 0)
        supported_samples = self._support_history.any(dim=-1).sum(dim=1)
        distinct_feet = self._support_history.any(dim=1).sum(dim=1)
        base_force = self.sensor.data.net_normal_forces_w_history.torch[:, :, self.base]
        base_collision = (torch.linalg.vector_norm(base_force, dim=-1) > 1).any(dim=(1, 2))
        timeout = env.episode_length_buf >= env.max_episode_length
        failure = base_collision | timeout | self.bypass
        self.success = (
            (self._window_count >= 10)
            & (supported_samples >= 5)
            & (distinct_feet >= 2)
            & support.any(dim=-1)
            & ~failure
        )
        self.ending = failure | self.success
        command = env.command_manager.get_command("base_velocity")
        v = asset.root_lin_vel_b.torch
        omega = asset.root_ang_vel_b.torch
        q = (
            torch.exp(-((command[:, :2] - v[:, :2]) ** 2).sum(dim=1) / 0.15)
            + 0.5 * torch.exp(-((command[:, 2] - omega[:, 2]) ** 2) / 0.15)
        ) / 1.5
        self.tracking_integral += q * env.step_dt
        self.duration += env.step_dt
        return self.success | self.bypass
