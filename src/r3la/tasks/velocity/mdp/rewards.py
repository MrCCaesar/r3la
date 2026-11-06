# Native managers resolve SceneEntityCfg defaults before term execution.
# ruff: noqa: B008
# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.managers import ManagerTermBase, RewardTermCfg, SceneEntityCfg
from isaaclab.utils.math import euler_xyz_from_quat, wrap_to_pi

from .observations import terrain_relative_height

if TYPE_CHECKING:
    from isaaclab.assets import Articulation
    from isaaclab.envs import ManagerBasedRLEnv
    from isaaclab.sensors import ContactSensor


def joint_pos_target_l2(env: ManagerBasedRLEnv, target: float, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Penalize joint position deviation from a target value."""
    # extract the used quantities (to enable type-hinting)
    asset: Articulation = env.scene[asset_cfg.name]
    # wrap the joint positions to (-pi, pi)
    joint_pos = wrap_to_pi(asset.data.joint_pos.torch[:, asset_cfg.joint_ids])
    # compute the reward
    return torch.sum(torch.square(joint_pos - target), dim=1)


def joint_deviation_l2(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    asset = env.scene[asset_cfg.name]
    """Penalize joint position deviation from default value."""
    return torch.sum(
        torch.square(
            asset.data.joint_pos.torch[:, asset_cfg.joint_ids]
            - asset.data.default_joint_pos.torch[:, asset_cfg.joint_ids]
        ),
        dim=1,
    )


def joint_power(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """Penalize absolute mechanical joint power."""
    asset = env.scene[asset_cfg.name]

    joint_torque = asset.data.applied_torque.torch[:, asset_cfg.joint_ids]
    joint_vel = asset.data.joint_vel.torch[:, asset_cfg.joint_ids]

    return torch.sum(
        torch.abs(joint_torque * joint_vel),
        dim=1,
    )


def _roll_pitch(env, asset_cfg=SceneEntityCfg("robot")):
    roll, pitch, _ = euler_xyz_from_quat(env.scene[asset_cfg.name].data.root_quat_w.torch)
    return wrap_to_pi(roll), wrap_to_pi(pitch)


def base_height_l2(env, target_height: float = 0.4):
    height, valid = terrain_relative_height(env)
    return torch.where(valid, (height - target_height).square(), 0.0).squeeze(-1)


def flat_orientation_l2(env, asset_cfg=SceneEntityCfg("robot")):
    roll, pitch = _roll_pitch(env, asset_cfg)
    return roll.square() + pitch.square()


def undesired_contacts(env, threshold: float, sensor_cfg: SceneEntityCfg):
    history = env.scene[sensor_cfg.name].data.net_normal_forces_w_history.torch[:, :, sensor_cfg.body_ids]
    return (torch.linalg.vector_norm(history, dim=-1).amax(dim=1) > threshold).sum(dim=1).float()


def feet_air_time(env, sensor_cfg: SceneEntityCfg, threshold: float = 0.5):
    sensor = env.scene[sensor_cfg.name]
    first = sensor.compute_first_contact(env.step_dt).torch[:, sensor_cfg.body_ids]
    last = sensor.data.last_air_time.torch[:, sensor_cfg.body_ids]
    return ((last - threshold) * first).sum(dim=1)


def stance_base_height_orientation_exp(
    env,
    target_height: float,
    sigma_h: float,
    sigma_o: float,
    asset_cfg=SceneEntityCfg("robot"),
    contact_sensor_cfg=SceneEntityCfg("contact_forces", body_names=".*foot"),
    command_name: str = "base_velocity",
    command_threshold: float = 0.1,
    contact_threshold: float = 1.0,
):
    """S25/S67 static stance, using valid critic heights and world Euler angles."""
    height, valid = terrain_relative_height(env)
    roll, pitch = _roll_pitch(env, asset_cfg)
    forces = env.scene[contact_sensor_cfg.name].data.net_normal_forces_w.torch[:, contact_sensor_cfg.body_ids]
    contact = (torch.linalg.vector_norm(forces, dim=-1) > contact_threshold).all(dim=1)
    command = env.command_manager.get_command(command_name)
    low = (torch.linalg.vector_norm(command[:, :2], dim=1) < command_threshold) & (
        command[:, 2].abs() < command_threshold
    )
    reward = torch.exp(-(height[:, 0] - target_height).abs() / sigma_h) * torch.exp(
        -torch.sqrt(roll.square() + pitch.square()) / sigma_o
    )
    return torch.where(valid[:, 0] & contact & low, reward, 0.0)


def feet_stumble(
    env: ManagerBasedRLEnv,
    sensor_cfg: SceneEntityCfg,
    ratio: float = 4.0,
) -> torch.Tensor:
    """Penalize foot collisions with large horizontal contact forces.

    Returns:
        Tensor of shape (num_envs,), containing the number of
        feet satisfying the stumble condition.
    """
    contact_sensor: ContactSensor = env.scene[sensor_cfg.name]

    # (num_envs, num_feet, 3)
    forces = contact_sensor.data.net_forces_w.torch[:, sensor_cfg.body_ids, :]

    # Horizontal contact force magnitude
    force_xy = torch.linalg.vector_norm(forces[..., :2], dim=-1)

    # Absolute vertical contact force
    force_z = torch.abs(forces[..., 2])

    # Stumble condition
    # better
    # stumble = (force_xy > ratio * force_z) & (torch.linalg.vector_norm(forces, dim=-1) > 1.0)
    stumble = force_xy > ratio * force_z

    # Sum over feet: (num_envs,)
    return torch.sum(stumble.float(), dim=1)


class action_smoothness_l2(ManagerTermBase):
    """Penalize the second-order difference of actions."""

    def __init__(
        self,
        cfg: RewardTermCfg,
        env: ManagerBasedRLEnv,
    ):
        super().__init__(cfg, env)

        actions = env.action_manager.action
        # Store action from two steps ago.
        self.prev_prev_action = torch.zeros_like(actions)

    def reset(self, env_ids: torch.Tensor | None = None):
        if env_ids is None:
            env_ids = slice(None)

        self.prev_prev_action[env_ids] = 0.0

    def __call__(
        self,
        env: ManagerBasedRLEnv,
    ) -> torch.Tensor:
        action = env.action_manager.action
        prev_action = env.action_manager.prev_action

        # Second-order action difference.
        diff = action - 2.0 * prev_action + self.prev_prev_action

        reward = torch.sum(torch.square(diff), dim=1)

        # Update history for the next step.
        self.prev_prev_action.copy_(prev_action)

        return reward
