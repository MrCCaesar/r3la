"""Owned sample storage; scheduling remains entirely in native SensorBase."""

from dataclasses import dataclass

import torch
import warp as wp


@dataclass(frozen=True)
class SensorSample:
    """Borrowed tensors, stable until own-row capture/reset. Clone retained trajectories.

    Values are float32 metres, masks bool; times float32 seconds since row reset,
    episode_id int64 [N], captured bool [N]. Spatial shapes follow each sensor.
    """

    values: torch.Tensor
    valid: torch.Tensor
    capture_time: torch.Tensor
    age: torch.Tensor
    episode_id: torch.Tensor
    captured: torch.Tensor


class _HeldSample:
    """Shared storage and reset bookkeeping, with no independent sampling clock."""

    def _initialize_sample(self, shape):
        self._values = torch.zeros(shape, device=self._device, dtype=torch.float32)
        self._valid = torch.zeros(shape, device=self._device, dtype=torch.bool)
        self._capture_time = torch.zeros(self._num_envs, device=self._device)
        self._captured = torch.zeros(self._num_envs, device=self._device, dtype=torch.bool)
        self._episode_id = torch.zeros(self._num_envs, device=self._device, dtype=torch.int64)

    def _store_sample(self, env_mask, values, valid):
        mask = wp.to_torch(env_mask)
        # Fixed-shape selection avoids dynamic nonzero allocations on every read.
        spatial_mask = mask.reshape((-1,) + (1,) * (values.ndim - 1))
        self._values.copy_(torch.where(spatial_mask, values, self._values))
        self._valid.copy_(torch.where(spatial_mask, valid, self._valid))
        self._capture_time.copy_(torch.where(mask, wp.to_torch(self._timestamp), self._capture_time))
        self._captured.logical_or_(mask)

    def read_sample(self) -> SensorSample:
        """Read via native lazy scheduling; no physics advancement or new clock."""
        _ = self.data
        return SensorSample(
            self._values,
            self._valid,
            self._capture_time,
            wp.to_torch(self._timestamp) - self._capture_time,
            self._episode_id,
            self._captured,
        )

    def reset(self, env_ids=None, env_mask=None):
        mask = self._resolve_indices_and_mask(env_ids, env_mask)
        super().reset(env_mask=mask)
        selected = wp.to_torch(mask)
        self._episode_id.add_(selected.to(torch.int64))
        self._captured.logical_and_(~selected)
        spatial_mask = selected.reshape((-1,) + (1,) * (self._values.ndim - 1))
        self._values.masked_fill_(spatial_mask, 0.0)
        self._valid.masked_fill_(spatial_mask, False)
        self._capture_time.masked_fill_(selected, 0.0)
