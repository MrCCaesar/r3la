# ruff: noqa: E402
"""Bounded T12 deterministic evaluation, full output and optional native wrapper check."""

import argparse
import json
import sys

import warp as wp

wp.config.enable_backward = False

import gymnasium as gym
import torch

from isaaclab.app import add_launcher_args, launch_simulation

from isaaclab_tasks.utils import resolve_task_config

import r3la.tasks  # noqa: F401
from r3la.tasks.velocity.config.Unitree.evaluation import configure_parkour_evaluation

parser = argparse.ArgumentParser()
parser.add_argument("--family", default="box")
parser.add_argument("--mirror", type=int, default=1)
parser.add_argument("--level", type=int, default=9)
parser.add_argument("--endpoint", action="store_true")
parser.add_argument("--wrapper", action="store_true")
add_launcher_args(parser)
args = parser.parse_args()
sys.argv = [sys.argv[0]]
cfg, _ = resolve_task_config("R3la-SWAP-Parkour-UnitreeGo2", "")
configure_parkour_evaluation(cfg, args.family, args.level, 1.0, args.mirror, seed=7)
cfg.sim.device = args.device
if args.endpoint:
    cfg.scene.terrain.terrain_generator.difficulty_range = (1.0, 1.0)


def check_outputs(obs):
    assert set(obs) == {"proprio", "commands", "privilege", "target", "amp"}
    assert obs["proprio"].shape == (2, 210) and obs["privilege"].shape == (2, 273)
    torch.testing.assert_close(obs["commands"], torch.tensor([[1.0, 0.0, 0.0]], device=cfg.sim.device).repeat(2, 1))
    for key in ("proprio", "commands", "privilege"):
        assert torch.isfinite(obs[key]).all()
    for key, value in obs["target"].items():
        assert value.dtype == torch.float32 and torch.isfinite(value).all(), key


with launch_simulation(cfg, args):
    env = gym.make("R3la-SWAP-Parkour-UnitreeGo2", cfg=cfg).unwrapped
    try:
        obs, _ = env.reset()
        check_outputs(obs)
        terrain, robot = env.scene.terrain, env.scene["robot"]
        assert terrain.terrain_levels.tolist() == [args.level, args.level]
        assert not env.curriculum_manager.active_terms
        spawn = terrain.task_spawn_pos[args.level, 0] + torch.tensor([0.0, 0.0, 0.4], device=env.device)
        torch.testing.assert_close(robot.data.root_pos_w.torch, spawn.repeat(2, 1), atol=1e-5, rtol=0)
        torch.testing.assert_close(robot.data.joint_pos.torch, robot.data.default_joint_pos.torch)
        assert torch.count_nonzero(robot.data.joint_vel.torch) == 0
        assert torch.count_nonzero(obs["privilege"][:, 32:35]) == 0
        assert env.scene["terrain_height_scanner"].read_sample().valid.all()
        assert env.scene["body_height_scanner"].read_sample().valid.all()
        initial = {key: obs[key].clone() for key in ("proprio", "commands", "privilege")}
        initial_amp = {key: value.clone() for key, value in obs["amp"].items()}
        obs, _ = env.reset()
        for key, value in initial.items():
            torch.testing.assert_close(obs[key], value, rtol=0, atol=0)
        for key, value in initial_amp.items():
            torch.testing.assert_close(obs["amp"][key], value, rtol=0, atol=0)
        for _ in range(6):
            obs, reward, terminated, truncated, _ = env.step(torch.zeros(2, 12, device=env.device))
            check_outputs(obs)
            assert torch.isfinite(reward).all() and not (terminated | truncated).any()
        assert terrain.terrain_levels.tolist() == [args.level, args.level]
        record = terrain.task_regions[args.level, 0]
        layout = record.layout
        if args.family in ("stairs", "tilted_stairs"):
            # Query the actual platform, including d=1 max-height fixture, with approved reach.
            center = layout.support_surface.xy_bounds.mean(axis=0)
            top = -layout.support_surface.offset
            if args.endpoint:
                assert abs(top - 2.53) < 1e-6
            pose = robot.data.root_pose_w.torch.clone()
            local = torch.tensor([*center, top + 0.4], device=env.device, dtype=torch.float32)
            transform = terrain.task_tile_to_world[args.level, 0]
            pose[:, :3] = (transform[:3, :3] @ local + transform[:3, 3]).repeat(2, 1)
            pose[:, 3:7] = torch.tensor([0.0, 0.0, 0.0, 1.0], device=env.device)
            robot.write_root_pose_to_sim(pose)
            sensor = env.scene["terrain_height_scanner"]
            sensor.reset()
            sample = sensor.read_sample()
            assert sample.valid[:, 93].all()
            torch.testing.assert_close(
                sample.values[:, 93], torch.full((2,), 0.4, device=env.device), atol=1e-5, rtol=0
            )
            print("platform ray coverage PASS", "height", top)
        print(
            "EVALUATION_RECORD",
            json.dumps(
                {
                    "family": layout.family,
                    "level": args.level,
                    "mirror": layout.mirror_sign,
                    "canonical_id": layout.canonical_id,
                    "difficulty": layout.difficulty,
                    "endpoint": args.endpoint,
                }
            ),
        )
        if args.wrapper:
            from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

            wrapped = RslRlVecEnvWrapper(env, clip_actions=None)
            tensor_dict = wrapped.get_observations()
            assert tensor_dict["target", "depth_image"].shape == (2, 240, 320, 1)
            env.episode_length_buf[0] = env.max_episode_length - 1
            returned, reward, done, extras = wrapped.step(torch.zeros(2, 12, device=env.device))
            assert done.tolist() == [1, 0] and extras["time_outs"].tolist() == [True, False]
            assert not extras.get("final_obs")
            assert "metadata" not in returned
            assert env.scene["front_camera"].read_sample().capture_time[0] == 0
            print("native RSL-RL TensorDict + timeout forwarding PASS; learner bootstrap outside scope")
        print("T12 PASS", args.family, "mirror", args.mirror, "endpoint", args.endpoint)
    finally:
        env.close()
