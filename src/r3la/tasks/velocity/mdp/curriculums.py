"""Persistent independent terrain-success windows and velocity-tracking batches."""

from collections import deque

import torch

from isaaclab.managers import ManagerTermBase


class ParkourCurriculum(ManagerTermBase):
    """Consume native pre-reset ending rows, in ascending environment ID order.

    Native reset clears the attempt owner immediately afterwards. There is no
    finalized-record queue, consumed flag or second episode scheduler.
    """

    def __init__(self, cfg, env):
        super().__init__(cfg, env)
        levels = env.scene.terrain.task_family_id.shape[0]
        command_cfg = env.command_manager.get_term("base_velocity").cfg
        self.min_speed, self.max_speed = command_cfg.min_speed, command_cfg.max_speed
        self.speed_upper_bounds = torch.full((6,), command_cfg.initial_speed, device=env.device)
        self.terrain_windows = [[deque(maxlen=100) for _ in range(levels)] for _ in range(6)]
        self.speed_batches = [[] for _ in range(6)]
        self.terrain_attempt_count = torch.zeros(6, levels, dtype=torch.int64, device=env.device)
        self.terrain_success_rate = torch.zeros(6, levels, device=env.device)

    def reset(self, env_ids=None):
        """Statistics and bounds intentionally persist across native episode resets."""
        return {}

    def __call__(self, env, env_ids):
        terrain = env.scene.terrain
        attempt = env.termination_manager.get_term_cfg("parkour_attempt").func
        ids = torch.arange(env.num_envs, device=env.device)[env_ids]
        ids = ids[attempt.ending[ids]].unique(sorted=True)
        # A pre-reset callback is infrequent; transfer the bounded ending records once.
        levels = terrain.terrain_levels[ids]
        families = terrain.task_family_id[levels, terrain.terrain_types[ids]]
        records = (
            torch.stack(
                (ids, levels, families, attempt.success[ids], attempt.duration[ids], attempt.tracking_integral[ids]),
                dim=1,
            )
            .cpu()
            .tolist()
        )
        level_count = terrain.task_family_id.shape[0]
        for env_id, level, family, success, duration, integral in records:
            env_id, level, family = int(env_id), int(level), int(family)
            window = self.terrain_windows[family][level]
            window.append(bool(success))
            rate = sum(window) / len(window)
            self.terrain_attempt_count[family, level] = len(window)
            self.terrain_success_rate[family, level] = rate
            next_level = level
            if len(window) >= 20:
                if rate >= 0.8:
                    next_level = level + 1
                    if next_level >= level_count:
                        next_level = int(torch.randint(level_count - 1, ()).item()) if level_count > 1 else 0
                elif rate <= 0.3:
                    next_level = max(0, level - 1)
            # Float32 sums of exactly fifty .02 s intervals can fall just below 1.
            if duration >= 1.0 - 1e-6:
                batch = self.speed_batches[family]
                batch.append(integral / duration)
                if len(batch) == 20:
                    mean = sum(batch) / 20
                    # Preserve inclusive thresholds after float32 integral readback.
                    delta = 0.1 if mean >= 0.8 - 1e-7 else (-0.1 if mean <= 0.3 + 1e-7 else 0.0)
                    self.speed_upper_bounds[family] = (self.speed_upper_bounds[family] + delta).clamp(
                        self.min_speed, self.max_speed
                    )
                    batch.clear()
            terrain.terrain_levels[env_id] = next_level
            terrain.env_origins[env_id] = terrain.terrain_origins[next_level, terrain.terrain_types[env_id]]
        return {
            "speed_upper_bounds": self.speed_upper_bounds.clone(),
            "terrain_attempt_count": self.terrain_attempt_count.clone(),
            "terrain_success_rate": self.terrain_success_rate.clone(),
        }
