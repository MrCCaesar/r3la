# ruff: noqa: E402
"""Bounded native T08 history/action check; explicitly run outside CPU test collection."""

import argparse
import sys

import warp as wp

wp.config.enable_backward = False

import gymnasium as gym
import torch

from isaaclab.app import add_launcher_args, launch_simulation

from isaaclab_tasks.utils import resolve_task_config

import r3la.tasks  # noqa: F401
from r3la.tasks.velocity.mdp.actions import validate_parkour_actions

CANONICAL = [f"{leg}_{joint}_joint" for leg in ("FL", "FR", "RL", "RR") for joint in ("hip", "thigh", "calf")]
parser = argparse.ArgumentParser()
add_launcher_args(parser)
args = parser.parse_args()
sys.argv = [sys.argv[0]]
cfg, _ = resolve_task_config("R3la-SWAP-Parkour-UnitreeGo2", "")
cfg.scene.num_envs = 2
cfg.scene.terrain.terrain_generator.sub_terrains = {"box": cfg.scene.terrain.terrain_generator.sub_terrains["box"]}
cfg.scene.terrain.terrain_generator.num_rows = 2
cfg.scene.terrain.terrain_generator.num_cols = 1
cfg.sim.device = args.device
cfg.seed = 7


def frames(obs):
    assert obs["proprio"].shape == (2, 210) and obs["proprio"].dtype == torch.float32
    return obs["proprio"].reshape(2, 5, 42)


def check_measurement(env, obs, joint_ids):
    state = env.scene["robot"].data
    latest = frames(obs)[:, -1]
    clean = torch.cat(
        (
            state.root_ang_vel_b.torch,
            state.projected_gravity_b.torch,
            state.joint_pos.torch[:, joint_ids] - state.default_joint_pos.torch[:, joint_ids],
            state.joint_vel.torch[:, joint_ids] - state.default_joint_vel.torch[:, joint_ids],
            env.action_manager.action,
        ),
        dim=-1,
    )
    limits = torch.tensor([0.2] * 3 + [0.05] * 3 + [0.01] * 12 + [1.5] * 12 + [0.0] * 12, device=env.device)
    assert torch.all((latest - clean).abs() <= limits + 1e-5), "feature order/noise bounds mismatch"
    assert obs["commands"].shape == (2, 3)
    torch.testing.assert_close(obs["commands"], env.command_manager.get_command("base_velocity"), rtol=0, atol=0)
    assert torch.count_nonzero(obs["commands"][:, 1:]) == 0


with launch_simulation(cfg, args):
    env = gym.make("R3la-SWAP-Parkour-UnitreeGo2", cfg=cfg).unwrapped
    try:
        obs, _ = env.reset()
        robot = env.scene["robot"]
        ids, names = robot.find_joints(CANONICAL, preserve_order=True)
        assert names == CANONICAL
        action_term = env.action_manager.get_term("joint_pos")
        assert type(action_term).__name__ == "JointPositionAction"
        assert action_term.IO_descriptor.joint_names == CANONICAL
        initial = frames(obs).clone()
        torch.testing.assert_close(initial, initial[:, :1].expand(-1, 5, -1), rtol=0, atol=0)
        assert torch.count_nonzero(initial[:, :, 30:]) == 0
        check_measurement(env, obs, ids)
        assert not torch.allclose(
            torch.linalg.vector_norm(initial[:, -1, 3:6], dim=1), torch.ones(2, device=env.device), atol=1e-6
        )
        # Check affine processing beyond [-1,1] without ever advancing physics at that target.
        large = torch.zeros((2, 12), device=env.device)
        large[:, 1] = 2.0
        validate_parkour_actions(env, large)
        env.action_manager.process_action(large)
        expected = robot.data.default_joint_pos.torch[:, ids] + 0.5 * large
        torch.testing.assert_close(action_term.processed_actions, expected)
        torch.testing.assert_close(action_term.raw_actions, large, rtol=0, atol=0)
        obs, _ = env.reset()
        previous = frames(obs).clone()
        command = obs["commands"].clone()
        for index in range(3):
            action = torch.linspace(-0.12, 0.12, 12, device=env.device).repeat(2, 1) * (index + 1) / 3
            validate_parkour_actions(env, action)
            obs, _, terminated, truncated, extras = env.step(action)
            assert not (terminated | truncated).any()
            current = frames(obs)
            torch.testing.assert_close(current[:, :-1], previous[:, 1:], rtol=0, atol=0)
            torch.testing.assert_close(current[:, -1, 30:], action, rtol=0, atol=0)
            torch.testing.assert_close(
                action_term.processed_actions, robot.data.default_joint_pos.torch[:, ids] + 0.5 * action
            )
            torch.testing.assert_close(obs["commands"], command, rtol=0, atol=0)
            check_measurement(env, obs, ids)
            assert "final_obs" not in extras
            previous = current.clone()
        # Native manual reset computes all rows once: only row0 backfills, row1 retains its last4 frames.
        obs, _ = env.reset(env_ids=torch.tensor([0], device=env.device))
        current = frames(obs)
        torch.testing.assert_close(current[0], current[0, :1].expand(5, -1), rtol=0, atol=0)
        torch.testing.assert_close(current[1, :-1], previous[1, 1:], rtol=0, atol=0)
        assert torch.count_nonzero(current[0, :, 30:]) == 0
        torch.testing.assert_close(current[1, -1, 30:], action[1], rtol=0, atol=0)
        # Force one real timeout transition; returned done-row data must be new-episode observations.
        previous = current.clone()
        env.episode_length_buf[0] = env.max_episode_length - 1
        validate_parkour_actions(env, action)
        obs, _, terminated, truncated, extras = env.step(action)
        assert truncated[0] and not terminated[0] and not (terminated[1] | truncated[1])
        current = frames(obs)
        torch.testing.assert_close(current[0], current[0, :1].expand(5, -1), rtol=0, atol=0)
        assert torch.count_nonzero(current[0, :, 30:]) == 0
        torch.testing.assert_close(current[1, :-1], previous[1, 1:], rtol=0, atol=0)
        check_measurement(env, obs, ids)
        assert "final_obs" not in extras
        # The checked boundary rejects corrupt input without submitting it to a simulator.
        for bad in (torch.zeros((1, 12), device=env.device), torch.full((2, 12), float("nan"), device=env.device)):
            try:
                validate_parkour_actions(env, bad)
            except ValueError:
                pass
            else:
                raise AssertionError("bad action accepted by checked boundary")
        print(
            "T08 PASS: shared210 history, noise/order, native affine actions, partial reset, timeout new-episode rows"
        )
    finally:
        env.close()
