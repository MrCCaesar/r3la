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