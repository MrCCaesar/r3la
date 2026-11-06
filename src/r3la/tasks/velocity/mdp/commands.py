"""Family-specific forward sampler on the native CommandTerm countdown lifecycle."""

import math
from collections.abc import Sequence

import torch

from isaaclab.managers import CommandTerm, CommandTermCfg
from isaaclab.utils import configclass


@configclass
class ParkourVelocityCommandCfg(CommandTermCfg):
    """Bounds are m/s; evaluation_velocity selects a fixed forward command."""

    class_type: str = "{DIR}.commands:ParkourVelocityCommand"
    resampling_time_range: tuple[float, float] = (20.02, 20.02)
    initial_speed: float = 1.0
    min_speed: float = 1.0
    max_speed: float = 3.0
    evaluation_velocity: float | None = None
    debug_vis: bool = False


class ParkourVelocityCommand(CommandTerm):
    """No heading/standing overrides or duplicate tracking accumulator."""

    def __init__(self, cfg, env):
        bounds = (cfg.min_speed, cfg.initial_speed, cfg.max_speed)
        if not all(math.isfinite(x) and x >= 0 for x in bounds) or not bounds[0] <= bounds[1] <= bounds[2]:
            raise ValueError("Speed bounds must be finite, nonnegative and min <= initial <= max")
        period = env.max_episode_length_s + env.step_dt
        if not all(math.isfinite(x) and x >= period - 1e-8 for x in cfg.resampling_time_range):
            raise ValueError("Native resampling period must exceed the episode limit by at least one control step")
        if cfg.resampling_time_range[0] != cfg.resampling_time_range[1]:
            raise ValueError("Parkour command requires a fixed native resampling period")
        if cfg.evaluation_velocity is not None and not (
            math.isfinite(cfg.evaluation_velocity) and 0 <= cfg.evaluation_velocity <= cfg.max_speed
        ):
            raise ValueError("Evaluation velocity must be finite and in [0,max_speed]")
        super().__init__(cfg, env)
        self._command = torch.zeros(env.num_envs, 3, device=env.device)

    @property
    def command(self) -> torch.Tensor:
        return self._command

    def _resample_command(self, env_ids: Sequence[int] | slice):
        ids = torch.arange(self.num_envs, device=self.device)[env_ids]
        if self.cfg.evaluation_velocity is not None:
            self._command[ids, 0] = self.cfg.evaluation_velocity
        else:
            terrain = self._env.scene.terrain
            family = terrain.task_family_id[terrain.terrain_levels[ids], terrain.terrain_types[ids]]
            owner = self._env.curriculum_manager.cfg.terrain_levels.func
            self._command[ids, 0] = torch.rand(len(ids), device=self.device) * owner.speed_upper_bounds[family]
        self._command[ids, 1:] = 0

    def _update_metrics(self):
        pass

    def _update_command(self):
        pass
