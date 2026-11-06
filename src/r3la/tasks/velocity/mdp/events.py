import torch
import warp as wp

from isaaclab.envs.mdp.events import (
    randomize_rigid_body_material as NativeMaterialRandomizer,
)
from isaaclab.managers import EventTermCfg, ManagerTermBase, SceneEntityCfg


class randomize_shared_material(ManagerTermBase):
    """Sample one material per environment for all selected shapes.

    Cached values:
        [static_friction, dynamic_friction, restitution]
        Shape: (num_envs, 3)
    """

    def __init__(self, cfg: EventTermCfg, env):
        super().__init__(cfg, env)

        # Reuse official backend-specific binding and body mapping.
        self._native = NativeMaterialRandomizer(cfg, env)
        self._impl = self._native._impl
        self._backend = type(self._impl).__module__.split(".")[0]

        self.material_values = torch.full(
            (env.num_envs, 3),
            float("nan"),
            device=env.device,
        )

        if self._backend == "isaaclab_newton":
            manager = env.sim.physics_manager

            if type(manager).__name__ == "NewtonKaminoManager":
                raise NotImplementedError(
                    "Kamino does not support independent "
                    "per-environment material randomization."
                )

    def __call__(
        self,
        env,
        env_ids: torch.Tensor | slice | None,
        asset_cfg: SceneEntityCfg,
        static_friction_range: tuple[float, float],
        dynamic_friction_range: tuple[float, float],
        restitution_range: tuple[float, float],
        num_buckets: int,
        make_consistent: bool = True,
        nominal: bool = False,
    ) -> None:
        # Normalize environment IDs.
        all_ids = torch.arange(env.num_envs, device="cpu")
        if env_ids is None:
            ids = all_ids
        elif isinstance(env_ids, slice):
            ids = all_ids[env_ids]
        else:
            ids = env_ids.to(device="cpu", dtype=torch.long)

        if ids.numel() == 0:
            return

        if nominal:
            if self._backend != "isaaclab_newton":
                raise ValueError("Nominal material readback currently supports the approved Newton backend only")
            shapes = self._impl._shape_indices.to(env.device)
            friction = wp.to_torch(self._impl._friction_binding)[ids.to(env.device)[:, None], shapes]
            restitution = wp.to_torch(self._impl._restitution_binding)[ids.to(env.device)[:, None], shapes]
            if not (torch.allclose(friction, friction[:, :1].expand_as(friction))
                    and torch.allclose(restitution, restitution[:, :1].expand_as(restitution))):
                raise ValueError("Nominal foot materials must share one coefficient per environment")
            self.material_values[ids.to(env.device)] = torch.stack(
                (friction[:, 0], friction[:, 0], restitution[:, 0]), dim=-1
            )
            return  # Nominal evaluation reads authored parameters without writing/randomizing.

        # Sample exactly one material per environment.
        if self._backend in ("isaaclab_physx", "isaaclab_ov"):
            bucket_ids = torch.randint(
                0, num_buckets, (len(ids),), device="cpu"
            )
            samples = self._impl.material_buckets[bucket_ids]

        elif self._backend == "isaaclab_newton":
            def sample_uniform(bounds):
                low, high = bounds
                return low + (high - low) * torch.rand(
                    len(ids), device=env.device
                )

            friction = sample_uniform(static_friction_range)
            restitution = sample_uniform(restitution_range)

            # Newton has a single friction coefficient.
            samples = torch.stack(
                (friction, friction, restitution), dim=-1
            )

        else:
            raise NotImplementedError(self._backend)

        if self._backend == "isaaclab_physx":
            self._write_physx(ids, samples)

        elif self._backend == "isaaclab_newton":
            self._write_newton(ids, samples)

        elif self._backend == "isaaclab_ov":
            self._write_ovphysx(ids, samples)

        # Cache only after successful backend write.
        self.material_values[ids.to(env.device)] = samples.to(
            env.device
        )

    def _write_physx(self, ids, samples):
        impl = self._impl
        asset = impl.asset
        materials = wp.to_torch(
            asset.root_view.get_material_properties()
        )

        # Shape indices are in backend order.
        if impl.num_shapes_per_body is None:
            shape_ids = list(range(asset.root_view.max_shapes))
        else:
            shape_ids = []
            offsets = [0]
            for count in impl.num_shapes_per_body:
                offsets.append(offsets[-1] + count)

            for body_id in impl._backend_body_ids:
                shape_ids.extend(
                    range(offsets[body_id], offsets[body_id + 1])
                )

        if not shape_ids:
            raise ValueError("No collision shapes selected")

        # Reject compliant-contact encoding.
        if (materials[ids[:, None], shape_ids, 2] < 0).any():
            raise ValueError(
                "Selected shapes contain negative native "
                "restitution (compliant-contact stiffness)."
            )

        materials[ids[:, None], shape_ids] = samples[:, None, :]

        asset.root_view.set_material_properties(
            wp.from_torch(materials.contiguous(), dtype=wp.float32),
            wp.from_torch(
                ids.to(torch.int32).contiguous(), dtype=wp.int32
            ),
        )

    def _write_newton(self, ids, samples):
        from newton import ModelFlags

        impl = self._impl

        friction = wp.to_torch(impl._friction_binding)
        restitution = wp.to_torch(impl._restitution_binding)

        rows = ids.to(friction.device)
        shapes = impl._shape_indices.to(friction.device)
        data = samples.to(friction.device)

        if shapes.numel() == 0:
            raise ValueError("No collision shapes selected")

        friction[rows[:, None], shapes] = data[:, None, 0]
        restitution[rows[:, None], shapes] = data[:, None, 2]

        impl._newton_manager.add_model_change(
            ModelFlags.SHAPE_PROPERTIES
        )

    def _write_ovphysx(self, ids, samples):
        impl = self._impl
        view = impl._material_view

        if view is None:
            raise ValueError("No material binding selected")

        materials = wp.to_torch(
            view.get_attribute(impl._material_type)
        )

        # One binding row per selected body and environment,
        # or one row per whole articulation.
        rows_by_env = impl._material_rows_by_env[ids]
        rows = rows_by_env.flatten().to(materials.device)

        if rows.numel() == 0:
            raise ValueError("No collision shapes selected")

        if (materials[rows, :, 2] < 0).any():
            raise ValueError(
                "Selected shapes use compliant-contact restitution."
            )

        n_rows = rows_by_env.shape[1]
        data = samples.to(materials.device).repeat_interleave(
            n_rows, dim=0
        )

        materials[rows] = data[:, None, :]

        view.set_attribute(
            impl._material_type,
            wp.from_torch(
                materials.contiguous(), dtype=wp.float32
            ),
            indices=wp.from_torch(
                rows.to(torch.int32).contiguous(),
                dtype=wp.int32,
            ),
        )

def reset_parkour_state(env, env_ids, asset_cfg=None, nominal: bool = False):
    """Reset selected robots at their assigned task entrance, never at mesh origin."""
    from isaaclab.utils.math import quat_from_euler_xyz, sample_uniform

    if asset_cfg is None:
        asset_cfg = SceneEntityCfg("robot")
    if env_ids is None or isinstance(env_ids, slice):
        env_ids = torch.arange(env.num_envs, device=env.device)[env_ids if env_ids is not None else slice(None)]
    terrain = env.scene.terrain
    asset = env.scene[asset_cfg.name]
    if not hasattr(env, "_parkour_spawn_radius"):
        _validate_newton_spawn_footprint(env, asset)
    levels, columns = terrain.terrain_levels[env_ids], terrain.terrain_types[env_ids]
    spawn = terrain.task_spawn_pos[levels, columns]
    count = len(env_ids)
    pose = torch.zeros((count, 7), device=env.device)
    pose[:, :3] = spawn
    if not nominal:
        pose[:, :2] += sample_uniform(-0.2, 0.2, (count, 2), device=env.device)
    pose[:, 2] += 0.4
    zeros = torch.zeros(count, device=env.device)
    yaw = terrain.task_spawn_yaw[levels, columns]
    if not nominal:
        yaw = yaw + sample_uniform(-0.1, 0.1, (count,), device=env.device)
    pose[:, 3:] = quat_from_euler_xyz(zeros, zeros, yaw)
    asset.write_root_pose_to_sim(pose, env_ids=env_ids)
    asset.write_root_velocity_to_sim(torch.zeros((count, 6), device=env.device), env_ids=env_ids)
    joint_pos = asset.data.default_joint_pos[env_ids].clone()
    if not nominal:
        joint_pos *= sample_uniform(0.9, 1.1, joint_pos.shape, device=env.device)
    asset.write_joint_state_to_sim(joint_pos, torch.zeros_like(joint_pos), env_ids=env_ids)


def set_evaluation_terrain(env, env_ids, level: int):
    """Startup-only fixed assignment; native reset subsequently retains these rows."""
    terrain = env.scene.terrain
    if not 0 <= level < terrain.task_family_id.shape[0]:
        raise ValueError("Evaluation level is outside the generated terrain grid")
    ids = slice(None) if env_ids is None else env_ids
    terrain.terrain_levels[ids] = level
    terrain.env_origins[ids] = terrain.terrain_origins[level, terrain.terrain_types[ids]]


def _validate_newton_spawn_footprint(env, asset):
    """Bound every collision shape for all joint rotations using chain lengths.

    The triangle inequality bounds distance from root to a shape by parent/child
    joint-anchor lengths plus its local translation and collision sphere radius.
    This is conservative even outside the permitted reset joint perturbations.
    Native model fields are pinned to the inspected Newton source version.
    """
    import numpy as np

    model = env.sim.backend_manager.backend.model
    view = asset.root_view
    articulation_id = int(view.articulation_ids.numpy()[0, 0])
    start = int(model.articulation_start.numpy()[articulation_id])
    end = int(model.articulation_end.numpy()[articulation_id])
    parents = model.joint_parent.numpy()
    children = model.joint_child.numpy()
    anchor_p = model.joint_X_p.numpy()
    anchor_c = model.joint_X_c.numpy()
    distance = {}
    for joint in range(start, end):
        parent, child = int(parents[joint]), int(children[joint])
        if parent == -1:
            distance[child] = 0.0
        else:
            if parent not in distance:
                raise ValueError('parkour spawn: unsupported joint topology')
            distance[child] = (
                distance[parent] + np.linalg.norm(anchor_p[joint, :3]) + np.linalg.norm(anchor_c[joint, :3])
            )
    shape_bodies = model.shape_body.numpy()
    shape_transforms = model.shape_transform.numpy()
    radii = model.shape_collision_radius.numpy()
    # Include contact margins as well as physical collision geometry.
    margins = model.shape_margin.numpy()
    radius = max(
        distance[int(body)] + np.linalg.norm(shape_transforms[i, :3]) + radii[i] + max(0.0, margins[i])
        for i, body in enumerate(shape_bodies) if int(body) in distance
    )
    for record in env.scene.terrain.task_regions.flat:
        record.layout.validate_spawn_footprint(float(radius))
    env._parkour_spawn_radius = float(radius)
