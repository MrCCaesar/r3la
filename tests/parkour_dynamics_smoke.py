# ruff: noqa: E402
"""Bounded T10/T11 applied parameters, clean outputs and native pre-reset ordering."""

import argparse
import sys

import warp as wp

wp.config.enable_backward = False

import gymnasium as gym
import torch

from isaaclab.actuators.newton import read_group_parameter
from isaaclab.app import add_launcher_args, launch_simulation
from isaaclab.utils.math import quat_apply

from isaaclab_tasks.utils import resolve_task_config

import r3la.tasks  # noqa: F401
from r3la.tasks.velocity.mdp.rewards import base_height_l2, stance_base_height_orientation_exp

parser = argparse.ArgumentParser()
add_launcher_args(parser)
args = parser.parse_args()
sys.argv = [sys.argv[0]]
cfg, _ = resolve_task_config("R3la-SWAP-Parkour-UnitreeGo2", "")
cfg.scene.num_envs = 2
generator = cfg.scene.terrain.terrain_generator
generator.sub_terrains = {"box": generator.sub_terrains["box"]}
generator.num_rows, generator.num_cols = 2, 1
cfg.scene.terrain.max_init_terrain_level = 0
cfg.sim.device = args.device
cfg.seed = 7


def check_clean(env, obs):
    assert set(obs) == {"proprio", "commands", "privilege", "amp", "target"}
    assert obs["privilege"].shape == (2, 273)
    amp, state = obs["amp"], env.scene["robot"].data
    expected = {
        "base_pos_w": (2, 3),
        "base_quat_w": (2, 4),
        "base_lin_vel_b": (2, 3),
        "base_ang_vel_b": (2, 3),
        "joint_pos": (2, 12),
        "joint_vel": (2, 12),
        "foot_pos_b": (2, 4, 3),
        "base_height": (2, 1),
        "base_height_valid": (2, 1),
    }
    assert set(amp) == set(expected)
    for key, shape in expected.items():
        assert amp[key].shape == shape
        assert amp[key].dtype == (torch.bool if key.endswith("valid") else torch.float32)
    torch.testing.assert_close(amp["base_pos_w"], state.root_pos_w.torch)
    torch.testing.assert_close(amp["base_quat_w"], state.root_quat_w.torch[:, [3, 0, 1, 2]])
    torch.testing.assert_close(obs["privilege"][:, 38:41], amp["base_lin_vel_b"])
    torch.testing.assert_close(obs["privilege"][:, 41:44], amp["base_ang_vel_b"])
    torch.testing.assert_close(obs["privilege"][:, 47:50], obs["commands"])
    feet, _ = env.scene["robot"].find_bodies(["FL_foot", "FR_foot", "RL_foot", "RR_foot"], preserve_order=True)
    reconstructed = (
        quat_apply(
            state.root_quat_w.torch[:, None].expand(-1, 4, -1).reshape(-1, 4), amp["foot_pos_b"].reshape(-1, 3)
        ).reshape(2, 4, 3)
        + state.root_pos_w.torch[:, None]
    )
    torch.testing.assert_close(reconstructed, state.body_pos_w.torch[:, feet], atol=1e-5, rtol=0)
    latest_contacts = env.scene["contact_forces"].data.net_normal_forces_w.torch
    links, _ = env.scene["contact_forces"].find_bodies(
        [f"{leg}_{link}" for link in ("thigh", "calf") for leg in ("FL", "FR", "RL", "RR")], preserve_order=True
    )
    torch.testing.assert_close(
        obs["privilege"][:, :8], (torch.linalg.vector_norm(latest_contacts[:, links], dim=-1) > 1).float()
    )


with launch_simulation(cfg, args):
    env = gym.make("R3la-SWAP-Parkour-UnitreeGo2", cfg=cfg).unwrapped
    try:
        obs, _ = env.reset()
        check_clean(env, obs)
        robot = env.scene["robot"]
        gains = env.event_manager.get_term_cfg("actuator_gains").func
        applied = obs["privilege"][:, 8:38].clone()
        for group in robot.actuators._native_group_names:
            ids = robot.actuators._group_joint_indices[group]
            kp = read_group_parameter(robot.actuators, group, "drive", "kp")
            kd = read_group_parameter(robot.actuators, group, "drive", "kd")
            torch.testing.assert_close(obs["privilege"][:, 8:20][:, ids], kd)
            torch.testing.assert_close(obs["privilege"][:, 20:32][:, ids], kp)
            for values, default in (
                (kp, gains.default_actuator_stiffness[group]),
                (kd, gains.default_actuator_damping[group]),
            ):
                ratio = values / default
                assert torch.all((ratio >= 0.8) & (ratio <= 1.2))
                assert torch.unique(ratio).numel() > 1
        mass = env.event_manager.get_term_cfg("base_mass").func
        base, _ = robot.find_bodies("base")
        ratio = robot.data.body_mass.torch[:, base] / mass.default_mass[:, base]
        assert torch.all((ratio >= 0.9) & (ratio <= 1.1))
        torch.testing.assert_close(obs["privilege"][:, 35:36], robot.data.body_mass.torch[:, base])
        com = env.event_manager.get_term_cfg("base_com").func
        offset = robot.data.body_com_pose_b.torch[:, base, :3] - com.default_com[:, base, :3]
        torch.testing.assert_close(obs["privilege"][:, 32:35], offset[:, 0])
        assert torch.all(offset.abs() <= torch.tensor([0.05, 0.05, 0.01], device=env.device))
        material = env.event_manager.get_term_cfg("physics_material").func
        impl = material._impl
        friction, restitution = wp.to_torch(impl._friction_binding), wp.to_torch(impl._restitution_binding)
        shapes = impl._shape_indices.to(env.device)
        torch.testing.assert_close(friction[:, shapes], obs["privilege"][:, 37:38].expand(-1, len(shapes)))
        torch.testing.assert_close(restitution[:, shapes], obs["privilege"][:, 36:37].expand(-1, len(shapes)))
        assert torch.all((applied[:, -1] >= 0.4) & (applied[:, -1] <= 1.2))
        assert torch.all((applied[:, -2] >= 0) & (applied[:, -2] <= 0.1))
        print("T10 applied P/D, mass, COM, shared foot materials and clean privilege/AMP PASS")

        # Twenty ending attempts trigger both decisions; only the ending row migrates.
        owner = env.curriculum_manager.cfg.terrain_levels.func
        owner.terrain_windows[0][0].extend([True] * 19)
        owner.speed_batches[0].extend([1.0] * 19)
        command = obs["commands"].clone()
        action = torch.zeros(2, 12, device=env.device)
        for step in range(50):
            if step == 49:
                env.episode_length_buf[0] = env.max_episode_length - 1
            obs, reward, terminated, truncated, _ = env.step(action)
            assert torch.isfinite(reward).all()
            if step < 49:
                assert not (terminated | truncated).any()
                torch.testing.assert_close(obs["commands"], command)
        assert truncated[0] and not terminated[0] and not (terminated | truncated)[1]
        assert env.scene.terrain.terrain_levels.tolist() == [1, 0]
        assert len(owner.terrain_windows[0][0]) == 20 and not owner.speed_batches[0]
        torch.testing.assert_close(owner.speed_upper_bounds[0], torch.tensor(1.1, device=env.device))
        torch.testing.assert_close(obs["commands"][1], command[1])
        torch.testing.assert_close(obs["privilege"][:, 8:38], applied, rtol=0, atol=0)
        spawn = env.scene.terrain.task_spawn_pos[1, 0]
        assert torch.all((robot.data.root_pos_w.torch[0, :2] - spawn[:2]).abs() <= 0.2)
        check_clean(env, obs)
        print("T11 native terminal step >=1 s, pre-reset migration, fixed command and next-attempt bounds PASS")

        # A genuine no-hit critic sample suppresses height rewards, never causes a reset.
        pose = robot.data.root_pose_w.torch.clone()
        pose[:, 2] = 20.0
        robot.write_root_pose_to_sim(pose)
        env.scene["terrain_height_scanner"].reset()
        assert not env.scene["terrain_height_scanner"].read_sample().valid.any()
        assert torch.count_nonzero(base_height_l2(env)) == 0
        assert torch.count_nonzero(stance_base_height_orientation_exp(env, 0.4, 0.1, 0.1)) == 0
        _, _, terminated, truncated, _ = env.step(action)
        assert not (terminated | truncated).any()
        print("T10/T11 PASS: 2 envs, 51 physics control steps; all-invalid height contributes zero without reset")
    finally:
        env.close()
