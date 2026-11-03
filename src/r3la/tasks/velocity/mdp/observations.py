from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import ContactSensor
from .events import randomize_shared_material

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
    asset_cfg: SceneEntityCfg
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


def com_offset(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg,
    event_name: str = "base_com",
) -> torch.Tensor:
    """Return randomized base COM offset."""
    asset: Articulation = env.scene[asset_cfg.name]
    event = env.event_manager.get_term_cfg(event_name).func

    current_com = asset.data.body_com_pose_b.torch[
        :, asset_cfg.body_ids, :3
    ]

    if event.default_com is None:
        return torch.zeros(
            (env.num_envs, current_com.shape[1] * 3),
            device=current_com.device,
            dtype=current_com.dtype,
        )

    default_com = event.default_com[
        :, asset_cfg.body_ids, :3
    ]

    return (current_com - default_com).reshape(env.num_envs, -1)

def link_mass(
        env: ManagerBasedRLEnv,
        asset_cfg: SceneEntityCfg
) -> torch.Tensor:
    """Return randomized base mass."""
    asset: Articulation = env.scene[asset_cfg.name]
    return asset.data.body_mass[:, asset_cfg.body_ids].reshape(env.num_envs, -1)


def _get_material_cache(
    env: ManagerBasedRLEnv,
    event_name: str,
) -> torch.Tensor:
    """Get cached material parameters, allowing shape probing."""

    # ObservationManager is still being constructed.
    # No material randomization is required for shape inference.
    if getattr(env, "observation_manager", None) is None:
        return torch.zeros(
            (env.num_envs, 3),
            device=env.device,
            dtype=torch.float32,
        )

    event_cfg = env.event_manager.get_term_cfg(event_name)
    event = event_cfg.func

    if not isinstance(event, randomize_shared_material):
        raise TypeError(
            f"Event '{event_name}' must use randomize_shared_material"
        )

    values = event.material_values

    # During actual execution, uninitialized material is an error.
    if not torch.isfinite(values).all():
        raise RuntimeError(
            f"Material event '{event_name}' has not initialized "
            "all environment material values."
        )

    return values


def foot_friction(
    env: ManagerBasedRLEnv,
    event_name: str = "foot_material",
) -> torch.Tensor:
    """Static friction or Newton friction: (num_envs, 1)."""
    return _get_material_cache(env, event_name)[:, 0:1]


def foot_restitution(
    env: ManagerBasedRLEnv,
    event_name: str = "foot_material",
) -> torch.Tensor:
    """Restitution: (num_envs, 1)."""
    return _get_material_cache(env, event_name)[:, 2:3]
