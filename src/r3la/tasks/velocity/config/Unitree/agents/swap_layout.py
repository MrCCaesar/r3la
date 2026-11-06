# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Go2 task-side physical representation, independent of generic SE operators."""

from __future__ import annotations

import torch

JOINT_NAMES = [f"{leg}_{joint}_joint" for leg in ("FL", "FR", "RL", "RR") for joint in ("hip", "thigh", "calf")]


def make_swap_layout(*, obs, env) -> dict:
    """Declare current target leaves and latest proprio frame; never align timestamps.

    Action coordinates are the task's dimensionless relative joint targets; the
    environment applies its existing 0.5 rad scale and default-position offset.
    """

    def permutation(indices: list[int], signs: list[int] | None = None) -> torch.Tensor:
        matrix = torch.eye(len(indices))[indices]
        return matrix if signs is None else matrix * torch.tensor(signs)[:, None]

    b, w, c = (
        torch.diag(torch.tensor([1.0, -1.0, 1.0])),
        torch.diag(torch.tensor([-1.0, 1.0, -1.0])),
        torch.diag(torch.tensor([1.0, -1.0, -1.0])),
    )
    a = permutation([3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8], [-1, 1, 1] * 4)
    u = a.abs()

    def grid(nx: int, ny: int) -> torch.Tensor:
        return permutation(torch.arange(nx * ny).reshape(ny, nx).flip(0).flatten().tolist())

    def field(key: list[str], shape: list[int], names: list[str], units, frame, indices=None) -> dict:
        return dict(key=key, source_shape=shape, indices=indices, names=names, units=units, frames=frame)

    def vector(fields: list[dict], p: torch.Tensor) -> dict:
        return dict(fields=fields, transform=p.tolist(), center=[0.0] * p.shape[0], scale=[1.0] * p.shape[0])

    def names(prefix: str, n: int) -> list[str]:
        return [f"{prefix}.{i}" for i in range(n)]

    frame_names = (
        names("omega", 3)
        + names("gravity", 3)
        + [f"q.{j}" for j in JOINT_NAMES]
        + [f"dq.{j}" for j in JOINT_NAMES]
        + [f"action.{j}" for j in JOINT_NAMES]
    )
    frame_units = ["rad/s"] * 3 + ["1"] * 3 + ["rad"] * 12 + ["rad/s"] * 12 + ["1"] * 12
    proprio = field(
        ["proprio"],
        [210],
        [f"history.{t}.{name}" for t in range(5) for name in frame_names],
        frame_units * 5,
        "base/joint",
    )
    commands = field(["commands"], [3], ["vx", "vy", "yaw_rate"], ["m/s", "m/s", "rad/s"], "base")
    p42 = torch.block_diag(w, b, a, a, a)
    critic_p = torch.block_diag(
        permutation([1, 0, 3, 2, 5, 4, 7, 6]), u, u, b, torch.eye(3), b, w, b, c, a, a, a, grid(17, 11)
    )
    critic_names = (
        names("contact", 8)
        + [f"damping.{j}" for j in JOINT_NAMES]
        + [f"stiffness.{j}" for j in JOINT_NAMES]
        + names("com", 3)
        + ["mass", "restitution", "friction"]
        + names("v", 3)
        + names("omega", 3)
        + names("gravity", 3)
        + ["vx", "vy", "yaw_rate"]
        + [f"q.{j}" for j in JOINT_NAMES]
        + [f"dq.{j}" for j in JOINT_NAMES]
        + [f"action.{j}" for j in JOINT_NAMES]
        + names("terrain_height", 187)
    )
    critic_units = (
        ["1"] * 8
        + ["N*m*s/rad"] * 12
        + ["N*m/rad"] * 12
        + ["m"] * 3
        + ["kg", "1", "1"]
        + ["m/s"] * 3
        + ["rad/s"] * 3
        + ["1"] * 3
        + ["m/s", "m/s", "rad/s"]
        + ["rad"] * 12
        + ["rad/s"] * 12
        + ["1"] * 12
        + ["m"] * 187
    )
    heights = [field(["target", "body_height_scan"], [286], names("body_height", 286), "m", "base")]
    heights += [
        field(["target", f"{foot}_height_scan"], [25], names(f"{foot}_height", 25), "m", "base")
        for foot in ("lf", "rf", "lh", "rh")
    ]
    latest_vector = field(["proprio"], [210], frame_names[:6], frame_units[:6], "base", list(range(168, 174)))
    latest_joints = field(["proprio"], [210], frame_names[6:30], frame_units[6:30], "joint", list(range(174, 198)))
    # The task explicitly owns the joint ordering, action scaling and observation history.
    if env is not None:
        base = getattr(env, "unwrapped", env)
        action_cfg = base.cfg.actions.joint_pos
        if (
            list(action_cfg.joint_names) != JOINT_NAMES
            or not action_cfg.preserve_order
            or action_cfg.scale != 0.5
            or not action_cfg.use_default_offset
        ):
            raise ValueError("Go2 action order/scale/default offset differs from declared SWAP profile")
    return dict(
        schema_version=1,
        actor=vector([proprio, commands], torch.block_diag(torch.kron(torch.eye(5), p42), c)),
        critic=vector([field(["privilege"], [273], critic_names, critic_units, "base/joint")], critic_p),
        wm_proprio=vector([latest_vector, commands, latest_joints], torch.block_diag(w, b, c, a, a)),
        height=vector(heights, torch.block_diag(grid(22, 13), torch.kron(permutation([1, 0, 3, 2]), grid(5, 5)))),
        depth=dict(
            key=["target", "depth_image"],
            source_shape=[240, 320, 1],
            layout="NHWC",
            units="m",
            frame="camera",
            scale=5.0,
            center=0,
            reflection_axis="width",
        ),
        action=dict(dim=12, transform=a.tolist(), names=JOINT_NAMES, units="1", frames="joint_relative_target"),
    )


def swap_reference_config() -> dict:
    """Return the approved functional profile; these are not claimed paper hyperparameters."""
    return dict(
        layout=dict(factory="r3la.tasks.velocity.config.Unitree.agents.swap_layout:make_swap_layout", kwargs={}),
        world_model=dict(
            k=5,
            hidden_dim=128,
            latent_dim=32,
            proprio_embedding_dim=64,
            image_embedding_dim=128,
            hidden_dims=[128, 128],
            activation="elu",
            latent_std_floor=1e-3,
            initial_std=1.0,
            encoder=dict(
                channels=[8, 16, 16, 32, 32, 32], kernel_sizes=[[4, 4]] * 6, strides=[[2, 2]] * 6, paddings=[[1, 1]] * 6
            ),
            decoder=dict(
                channels=[32, 32, 16, 16, 8, 1],
                kernel_sizes=[[4, 4]] * 6,
                strides=[[2, 2]] * 6,
                paddings=[[1, 1]] * 6,
                output_paddings=[[1, 0], [1, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
            ),
            weights=dict(proprio=1.0, height=1.0, depth=1.0),
            sigma=dict(proprio=1.0, height=1.0, depth=1.0),
            beta=1.0,
        ),
        world_model_training=dict(
            learning_rate=3e-4, num_learning_epochs=1, sequence_length=5, batch_size=16, max_grad_norm=1.0
        ),
    )
