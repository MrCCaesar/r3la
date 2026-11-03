# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.managers import SceneEntityCfg, ManagerTermBase, RewardTermCfg
from isaaclab.utils.math import wrap_to_pi

if TYPE_CHECKING:
    from isaaclab.assets import Articulation
    from isaaclab.envs import ManagerBasedRLEnv
    from isaaclab.assets import Articulation, RigidObject
    from isaaclab.sensors import ContactSensor, RayCaster


def joint_pos_target_l2(
    env: ManagerBasedRLEnv, 
    target: float, 
    asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Penalize joint position deviation from a target value."""
    # extract the used quantities (to enable type-hinting)
    asset: Articulation = env.scene[asset_cfg.name]
    # wrap the joint positions to (-pi, pi)
    joint_pos = wrap_to_pi(asset.data.joint_pos.torch[:, asset_cfg.joint_ids])
    # compute the reward
    return torch.sum(torch.square(joint_pos - target), dim=1)


def joint_deviation_l2(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg) -> torch.Tensor:
    asset = env.scene[asset_cfg.name]
    """Penalize joint position deviation from default value."""
    return torch.sum(
        torch.square(asset.data.joint_pos.torch[:, asset_cfg.joint_ids] - asset.data.default_joint_pos.torch[:, asset_cfg.joint_ids]),
        dim=1,
    )

def joint_power(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """Penalize absolute mechanical joint power.
    """
    asset = env.scene[asset_cfg.name]

    joint_torque = asset.data.applied_torque.torch[:, asset_cfg.joint_ids]
    joint_vel = asset.data.joint_vel.torch[:, asset_cfg.joint_ids]

    return torch.sum(
        torch.abs(joint_torque * joint_vel),
        dim=1,
    )


def stance_base_height_orientation_exp(
    env: ManagerBasedRLEnv,
    target_height: float,
    sigma_h: float,
    sigma_o: float,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    sensor_cfg: SceneEntityCfg | None = None,
    contact_sensor_cfg: SceneEntityCfg = SceneEntityCfg("contact_forces"),
    command_name: str = "base_velocity",
    command_threshold: float = 0.1,
    contact_threshold: float = 1.0,
) -> torch.Tensor:
    """Reward static stance for base height and orientation using exp kernel
    when robot's all feet in contact and low command velocity.

    Returns:
        Tensor of shape (num_envs,).
    """
    asset = env.scene[asset_cfg.name]

    if sensor_cfg is not None:
        sensor: RayCaster = env.scene[sensor_cfg.name]
        ray_z = sensor.data.ray_hits_w.torch[..., 2]

        # Adjust the target height using the sensor data, ignoring rays that missed the terrain
        ray_hits_z = sensor.data.ray_hits_w.torch[..., 2]
        finite_hits = torch.isfinite(ray_hits_z)
        safe_hits = torch.where(finite_hits, ray_hits_z, torch.zeros_like(ray_hits_z))
        hit_count = finite_hits.sum(dim=1).clamp(min=1)
        terrain_height = safe_hits.sum(dim=1) / hit_count
        adjusted_target_height = target_height + terrain_height
    else:
       # Use the provided target height directly for flat terrain
       adjusted_target_height = target_height

    # Base height error.
    height = asset.data.root_pos_w.torch[:, 2]
    height_error = torch.abs(height - adjusted_target_height)

    # Base orientation error
    gravity_b = asset.data.projected_gravity_b.torch
    orientation_error = torch.atan2(
        torch.linalg.vector_norm(gravity_b[:, :2], dim=1),
        -gravity_b[:, 2],
    )

    # All four feet must be in contact.
    contact_sensor = env.scene[contact_sensor_cfg.name]
    foot_forces = contact_sensor.data.net_normal_forces_w.torch[:, contact_sensor_cfg.body_ids, :]

    all_feet_contact = (
        torch.linalg.vector_norm(foot_forces, dim=-1)
        > contact_threshold
    ).all(dim=1)

    # Low commanded velocity.
    commands = env.command_manager.get_command(command_name)

    low_command = (
        torch.linalg.vector_norm(commands[:, :2], dim=1)
        < command_threshold
    ) & (
        torch.abs(commands[:, 2]) < command_threshold
    )

    # Static stance indicator.
    stance = all_feet_contact & low_command

    reward = (
        torch.exp(-height_error / sigma_h)
        * torch.exp(-orientation_error / sigma_o)
    )

    return reward * stance.float()


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

        # Number of valid action samples in each episode.
        self.history_count = torch.zeros(
            env.num_envs,
            dtype=torch.long,
            device=env.device,
        )

    def reset(self, env_ids: torch.Tensor | None = None):
        if env_ids is None:
            env_ids = slice(None)

        self.prev_prev_action[env_ids] = 0.0
        self.history_count[env_ids] = 0

    def __call__(
        self,
        env: ManagerBasedRLEnv,
    ) -> torch.Tensor:
        action = env.action_manager.action
        prev_action = env.action_manager.prev_action

        # Second-order action difference.
        diff = (
            action
            - 2.0 * prev_action
            + self.prev_prev_action
        )

        reward = torch.sum(torch.square(diff), dim=1)

        # Disable penalty until 3 actions are available.
        reward = torch.where(
            self.history_count >= 2,
            reward,
            torch.zeros_like(reward),
        )

        # Update history for the next step.
        self.prev_prev_action.copy_(prev_action)
        self.history_count.add_(1)

        return reward