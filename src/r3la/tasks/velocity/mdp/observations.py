from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import ContactSensor

if TYPE_CHECKING:
    from isaaclab.assets import Articulation, RigidObject


def is_contact(
    env: ManagerBasedRLEnv,
    threshold: float,
    sensor_cfg: SceneEntityCfg,
) -> torch.Tensor:
    """Return binary contact states for the four thighs."""

    contact_sensor: ContactSensor = env.scene.sensors[sensor_cfg.name]

    # Shape: (num_envs, num_bodies, 3)
    forces = contact_sensor.data.net_normal_forces_w.torch

    # Select thigh bodies and calculate force magnitudes.
    forces = forces[:, sensor_cfg.body_ids, :]
    return (
        torch.linalg.norm(forces, dim=-1) > threshold
    ).float()


def actuator_gains(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg,
    actuator_name: str = "base_legs",
) -> torch.Tensor:
    """Get randomized actuator Kp and Kd."""
    asset: RigidObject | Articulation = env.scene[asset_cfg.name]

    default_joint_stiffness = asset.data.joint_stiffness.torch.clone()
    default_joint_damping = asset.data.joint_damping.torch.clone()

    # Ownership decides the gain source and write path per group: implicit groups are
    # articulation-owned, Newton-executed groups are controller-owned (their mapping
    # entries are the Newton actuator objects), and Lab explicit groups own their tensors.
    from isaaclab.actuators import IdealPDActuator  # noqa: PLC0415

    collection = asset.actuators
    _native_group_names = getattr(collection, "_native_group_names", set())
    _gain_actuators = {
        name: actuator
        for name, actuator in collection.items()
        if name in _native_group_names
        or getattr(actuator, "is_implicit_model", False)
        or isinstance(actuator, IdealPDActuator)
    }
    group_joint_indices = getattr(collection, "_group_joint_indices", None)
    _group_joint_indices = {
        name: (group_joint_indices[name] if group_joint_indices is not None else actuator.joint_indices)
        for name, actuator in _gain_actuators.items()
    }

    from isaaclab.actuators.newton import read_group_parameter  # noqa: PLC0415

    for name, actuator in _gain_actuators.items():
        joint_ids = _group_joint_indices[name]
        if name in _native_group_names:
            stiffness = read_group_parameter(collection, name, "drive", "kp")
            damping = read_group_parameter(collection, name, "drive", "kd")
        else:
            stiffness = actuator.stiffness
            damping = actuator.damping
        if not getattr(actuator, "is_implicit_model", False):
            # Explicit and Newton PD gains replace the zeroed solver gains in the defaults.
            default_joint_stiffness[:, joint_ids] = stiffness
            default_joint_damping[:, joint_ids] = damping

    return torch.cat((default_joint_stiffness[:, asset_cfg.joint_ids], default_joint_damping[:, asset_cfg.joint_ids]), dim=-1)
    