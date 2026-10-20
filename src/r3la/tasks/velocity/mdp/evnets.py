"""Single-joint motor failure and its current-strength observation (ENV-REQ1).

Strength columns follow articulation joint order, as do the task's actions and
joint observations. Consumers must treat ``env.motor_strengths`` as read-only.
Disable both ``events.weak_motor`` and ``observations.privilege.motor_strengths``
together. No event means no gain writes or synthetic strength state.
"""

from __future__ import annotations

import math
import operator
from functools import wraps
from typing import TYPE_CHECKING

import torch

from isaaclab.actuators import IdealPDActuator
from isaaclab.managers import ManagerTermBase, SceneEntityCfg

if TYPE_CHECKING:
    from collections.abc import Sequence

    from isaaclab.envs import ManagerBasedRLEnv
    from isaaclab.managers import EventTermCfg

__all__ = ["MotorFailure", "motor_strengths"]


def motor_strengths(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Read the currently applied strengths without sampling or changing state."""
    if not hasattr(env, "motor_strengths"):
        raise RuntimeError("motor_strengths requires MotorFailure; disable this observation with the event")
    return env.motor_strengths


class MotorFailure(ManagerTermBase):
    """Scale fixed PD baselines with one failure per reset or interval episode.

    Distribution parameters are mandatory in ``EventTermCfg.params``. Interval
    mode also requires a positive, finite ``interval_range_s``, per-environment
    timers, and resampling on reset. Repeated interval callbacks do no work once
    a row has failed. A reset-mode manager reset callback preserves the failure
    just applied by ``EventManager.apply("reset")``.
    """

    def __init__(self, cfg: EventTermCfg, env: ManagerBasedRLEnv):
        super().__init__(cfg, env)
        required = {"asset_cfg", "severe_prob", "severe_max", "mild_min"}
        if set(cfg.params) != required:
            raise ValueError(f"MotorFailure requires exactly these parameters: {sorted(required)}")
        values = [cfg.params[k] for k in ("severe_prob", "severe_max", "mild_min")]
        if any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in values):
            raise ValueError("MotorFailure distribution parameters must be finite numbers")
        self.severe_prob, self.severe_max, self.mild_min = values
        if not 0 <= self.severe_prob <= 1 or not 0 < self.severe_max < self.mild_min < 0.9:
            raise ValueError("MotorFailure requires 0<=severe_prob<=1 and 0<severe_max<mild_min<0.9")
        if cfg.mode not in ("reset", "interval") or cfg.min_step_count_between_reset != 0:
            raise ValueError("MotorFailure requires reset/interval mode and every-reset application")
        if cfg.mode == "interval":
            interval = cfg.interval_range_s
            if (
                not isinstance(interval, (tuple, list))
                or len(interval) != 2
                or any(not isinstance(t, (int, float)) or not math.isfinite(t) for t in interval)
                or not 0 < interval[0] <= interval[1]
            ):
                raise ValueError("MotorFailure interval_range_s must satisfy finite 0<t_min<=t_max")
            # EventManager samples timers in torch's default floating dtype.
            # A positive Python float can otherwise become zero or infinity.
            timer_bounds = torch.tensor(interval, dtype=torch.get_default_dtype())
            if not (torch.isfinite(timer_bounds).all() and (timer_bounds > 0).all()):
                raise ValueError("MotorFailure interval_range_s must be representable as finite positive timers")
            if cfg.is_global_time or not cfg.resample_interval_on_reset:
                raise ValueError("MotorFailure interval requires independent timers resampled on reset")
        if not isinstance(env.step_dt, (int, float)) or not math.isfinite(env.step_dt) or env.step_dt <= 0:
            raise ValueError("MotorFailure step_dt must be finite and positive")
        asset_cfg = cfg.params["asset_cfg"]
        # InteractiveScene supports keys()/string lookup, but not mapping membership.
        if not isinstance(asset_cfg, SceneEntityCfg) or asset_cfg.name not in env.scene.keys():  # noqa: SIM118
            raise ValueError("MotorFailure asset_cfg must select an existing articulation")
        self.asset = env.scene[asset_cfg.name]
        ids = asset_cfg.joint_ids
        ids = list(range(len(self.asset.joint_names)))[ids] if isinstance(ids, slice) else list(ids)
        try:
            ids = [operator.index(i) for i in ids]
        except TypeError as exc:
            raise ValueError("MotorFailure requires integer joint indices") from exc
        if len(ids) != 12 or len(set(ids)) != 12 or any(i < 0 or i >= len(self.asset.joint_names) for i in ids):
            raise ValueError("MotorFailure requires 12 distinct valid joints")
        self.joint_ids = sorted(ids)
        self.joint_names = tuple(self.asset.joint_names[i] for i in self.joint_ids)
        if hasattr(env, "motor_strengths"):
            raise ValueError("MotorFailure already configured for this environment")

        collection = self.asset.actuators
        native = getattr(collection, "_native_group_names", set())
        group_ids = getattr(collection, "_group_joint_indices", {})
        self.groups = []
        covered = []
        for name, actuator in collection.items():
            # Native entries expose their indices through the collection only.
            indices = group_ids[name] if name in group_ids else actuator.joint_indices  # noqa: SIM401
            indices = list(range(len(self.asset.joint_names)))[indices] if isinstance(indices, slice) else list(indices)
            pairs = [(local, self.joint_ids.index(int(j))) for local, j in enumerate(indices) if int(j) in ids]
            if not pairs:
                continue
            implicit = getattr(actuator, "is_implicit_model", False)
            if name in native:
                # The owner/selected backend is known before importing native dependencies.
                from isaaclab.actuators.newton import read_group_parameter

                kp = read_group_parameter(collection, name, "controller", "kp")
                kd = read_group_parameter(collection, name, "controller", "kd")
            elif implicit:
                if not (
                    callable(getattr(self.asset, "write_joint_stiffness_to_sim_index", None))
                    and callable(getattr(self.asset, "write_joint_damping_to_sim_index", None))
                ):
                    raise ValueError(f"MotorFailure missing implicit gain writers: {name}")
                kp = self.asset.data.joint_stiffness.torch[:, indices]
                kd = self.asset.data.joint_damping.torch[:, indices]
            elif isinstance(actuator, IdealPDActuator):
                kp, kd = actuator.stiffness, actuator.damping
            else:
                raise ValueError(f"MotorFailure unsupported gain owner: {name}")
            if (
                kp.shape != (env.num_envs, len(indices))
                or kd.shape != kp.shape
                or not kp.is_floating_point()
                or kp.dtype != kd.dtype
                or kp.device != torch.device(env.device)
                or kd.device != kp.device
            ):
                raise ValueError(f"MotorFailure invalid gain buffers: {name}")
            local, public = zip(*pairs, strict=True)
            local = torch.tensor(local, device=kp.device)
            public = torch.tensor(public, device=kp.device)
            physical = torch.tensor([indices[i] for i in local.tolist()], device=kp.device)
            self.groups.append(
                (
                    name,
                    actuator,
                    name in native,
                    implicit,
                    local,
                    public,
                    physical,
                    kp[:, local].clone(),
                    kd[:, local].clone(),
                )
            )
            covered.extend(public.tolist())
        if sorted(covered) != list(range(12)):
            raise ValueError("MotorFailure requires unique writable ownership of all 12 joints")
        dtype = self.groups[0][-2].dtype
        if any(group[-2].dtype != dtype for group in self.groups):
            raise ValueError("MotorFailure requires compatible gain dtypes")
        # Directed rounding keeps sampled values inside the mathematical failure bounds.
        hi = torch.tensor(self.severe_max, dtype=dtype)
        if hi.double().item() > self.severe_max:
            hi = torch.nextafter(hi, torch.tensor(0.0, dtype=dtype))
        lo = torch.tensor(self.mild_min, dtype=dtype)
        if lo.double().item() < self.mild_min:
            lo = torch.nextafter(lo, torch.tensor(float("inf"), dtype=dtype))
        mild_hi = torch.nextafter(torch.tensor(0.9, dtype=dtype), torch.tensor(0.0, dtype=dtype))
        tiny = torch.nextafter(torch.tensor(0.0, dtype=dtype), torch.tensor(1.0, dtype=dtype))
        if hi <= 0 or lo > mild_hi:
            raise ValueError("MotorFailure distribution interval is not representable in gain dtype")
        self._severe_hi, self._mild_lo, self._mild_hi, self._tiny = (x.item() for x in (hi, lo, mild_hi, tiny))
        self.alpha = torch.ones((env.num_envs, 12), device=env.device, dtype=dtype)
        self.triggered = torch.zeros(env.num_envs, device=env.device, dtype=torch.bool)
        self.selected_joint = torch.full((env.num_envs,), -1, device=env.device, dtype=torch.long)
        self._fresh_schedule = torch.ones_like(self.triggered)
        self._deadline = torch.zeros(env.num_envs, device=env.device, dtype=torch.float64)
        self._clock_bound = False
        env.motor_strengths = self.alpha

    def __call__(
        self,
        env: ManagerBasedRLEnv,
        env_ids: torch.Tensor | None,
        asset_cfg: SceneEntityCfg,
        severe_prob: float,
        severe_max: float,
        mild_min: float,
    ) -> None:
        rows = self._ids(env_ids)
        if self.cfg.mode == "reset":
            self._normal(rows)
        else:
            rows = rows[~self.triggered[rows]]
        if rows.numel() == 0:
            return
        joints = torch.randint(12, (len(rows),), device=self.alpha.device)
        severe = torch.rand(len(rows), device=self.alpha.device) < self.severe_prob
        u = torch.rand(len(rows), device=self.alpha.device, dtype=self.alpha.dtype)
        low = ((1 - u) * self._severe_hi).clamp_min(self._tiny)
        high = (self._mild_lo + u * (0.9 - self._mild_lo)).clamp_max(self._mild_hi)
        self.alpha[rows, joints] = torch.where(severe, low, high)
        self._apply(rows, joints if self.cfg.mode == "interval" else None)
        self.selected_joint[rows] = joints
        self.triggered[rows] = True

    def reset(self, env_ids: Sequence[int] | torch.Tensor | None = None) -> None:
        """Restore only interval rows; reset-mode faults have already been applied."""
        if self.cfg.mode == "reset":
            return
        rows = self._ids(env_ids)
        if rows.numel() == 0:
            return
        self._bind_clock()
        self._normal(rows)
        self._apply(rows)
        self.triggered[rows] = False
        self.selected_joint[rows] = -1
        self._fresh_schedule[rows] = True

    def _ids(self, env_ids) -> torch.Tensor:
        all_ids = torch.arange(self.num_envs, device=self.alpha.device)
        if env_ids is None:
            return all_ids
        if isinstance(env_ids, slice):
            return all_ids[env_ids]
        return torch.as_tensor(env_ids, device=self.alpha.device, dtype=torch.long)

    def _normal(self, rows: torch.Tensor) -> None:
        if rows.numel():
            self.alpha[rows] = 0.9 + 0.2 * torch.rand(len(rows), 12, device=self.alpha.device, dtype=self.alpha.dtype)

    def _apply(self, rows: torch.Tensor, joints: torch.Tensor | None = None) -> None:
        for name, owner, native, implicit, local, public, physical, kp0, kd0 in self.groups:
            selected = rows if joints is None else rows[torch.isin(joints, public)]
            if selected.numel() == 0:
                continue
            # Restrict interval writes to each failed column, preserving other joints exactly.
            for column in range(len(local)) if joints is not None else [None]:
                active = selected if column is None else rows[joints == public[column]]
                if active.numel() == 0:
                    continue
                cols = slice(None) if column is None else slice(column, column + 1)
                gains = self.alpha[active[:, None], public[cols]]
                kp, kd = gains * kp0[active, cols], gains * kd0[active, cols]
                if native:
                    from isaaclab.actuators.newton import write_group_parameter

                    write_group_parameter(
                        self.asset.actuators, name, "controller", "kp", kp, env_ids=active, joint_ids=local[cols]
                    )
                    write_group_parameter(
                        self.asset.actuators, name, "controller", "kd", kd, env_ids=active, joint_ids=local[cols]
                    )
                elif implicit:
                    self.asset.write_joint_stiffness_to_sim_index(
                        stiffness=kp, env_ids=active, joint_ids=physical[cols]
                    )
                    self.asset.write_joint_damping_to_sim_index(damping=kd, env_ids=active, joint_ids=physical[cols])
                    owner.stiffness[active[:, None], local[cols]] = kp
                    owner.damping[active[:, None], local[cols]] = kd
                else:
                    owner.stiffness[active[:, None], local[cols]] = kp
                    owner.damping[active[:, None], local[cols]] = kd

    def _bind_clock(self) -> None:
        """Correct only this term's timer for same-step automatic resets.

        EventManager samples the original times. Its apply() normally subtracts
        dt even for rows just reset in that step, and uses a 1e-6 early cutoff.
        Derive this term's due rows from completed episode steps instead. The
        wrapper forwards all modes/other terms to the unchanged manager. It is
        installed once per environment, whose simulation loop is sequential.
        """
        manager = getattr(self._env, "event_manager", None)
        if self._clock_bound or manager is None:
            return
        index = next(i for i, cfg in enumerate(manager._mode_term_cfgs["interval"]) if cfg.func is self)
        apply = manager.apply

        @wraps(apply)
        def apply_with_episode_clock(mode, env_ids=None, dt=None, global_env_step_count=None):
            if mode == "interval" and dt is not None:
                timer = manager._interval_term_time_left[index]
                self._deadline[self._fresh_schedule] = timer[self._fresh_schedule].double()
                self._fresh_schedule[:] = False
                remaining = self._deadline - self._env.episode_length_buf.double() * self._env.step_dt
                waiting_timer = torch.where(remaining > 0, dt + remaining.clamp_min(2e-6), 0).to(timer.dtype)
                timer.copy_(torch.where(self.triggered, timer, waiting_timer))
            return apply(mode, env_ids=env_ids, dt=dt, global_env_step_count=global_env_step_count)

        manager.apply = apply_with_episode_clock
        self._clock_bound = True
