# ruff: noqa: E402
"""Bounded T09 native capture/reset/calibration checks; not pytest collection."""

import argparse
import sys

import warp as wp

wp.config.enable_backward = False

import gymnasium as gym
import torch

from isaaclab.app import add_launcher_args, launch_simulation
from isaaclab.utils.math import quat_apply_yaw, quat_from_euler_xyz

from isaaclab_tasks.utils import resolve_task_config

import r3la.tasks  # noqa: F401
from r3la.tasks.velocity.mdp.sensor_observations import read_low_rate_targets

parser = argparse.ArgumentParser()
parser.add_argument("--debug-outputs", action="store_true")
add_launcher_args(parser)
args = parser.parse_args()
sys.argv = [sys.argv[0]]
cfg, _ = resolve_task_config("R3la-SWAP-Parkour-UnitreeGo2", "")
cfg.scene.num_envs = 2
generator = cfg.scene.terrain.terrain_generator
generator.sub_terrains = {"box": generator.sub_terrains["box"]}
generator.num_rows, generator.num_cols = 2, 1
generator.difficulty_range = (1.0, 1.0)
cfg.sim.device = args.device
cfg.seed = 7
if args.debug_outputs:
    cfg.scene.front_camera.data_types = [
        "distance_to_image_plane", "rgb", "rgba", "rgb_hdr", "albedo", "depth",
        "distance_to_camera", "normals", "semantic_segmentation", "instance_segmentation",
    ]
# Test-only fixture with the same optics/axes, translated clear of the Go2 head.
# Production front_camera uses the user-corrected x=0.35 m mount.
cfg.scene.calibration_camera = cfg.scene.front_camera.replace(
    prim_path="{ENV_REGEX_NS}/Robot/base/calibration_camera",
    offset=cfg.scene.front_camera.offset.replace(pos=(0.6, 0.0, 0.05)),
)


def clone_targets(env):
    bundle = read_low_rate_targets(env)
    return {key: value.clone() for key, value in bundle.target.items()}


with launch_simulation(cfg, args):
    env = gym.make("R3la-SWAP-Parkour-UnitreeGo2", cfg=cfg).unwrapped
    try:
        obs, _ = env.reset()
        expected = {
            "depth_image": (2, 240, 320, 1),
            "body_height_scan": (2, 286),
            "lf_height_scan": (2, 25),
            "rf_height_scan": (2, 25),
            "lh_height_scan": (2, 25),
            "rh_height_scan": (2, 25),
        }
        for key, shape in expected.items():
            assert obs["target"][key].shape == shape and obs["target"][key].dtype == torch.float32
            assert torch.isfinite(obs["target"][key]).all()
        metadata = obs["metadata"]
        assert metadata["low_rate_valid"].all()
        assert metadata["episode_id"].dtype == torch.int64
        assert torch.count_nonzero(metadata["low_rate_capture_time"]) == 0
        assert torch.count_nonzero(metadata["low_rate_age"]) == 0
        assert metadata["critic_height_valid"].shape == (2, 187)
        camera = env.scene["front_camera"]
        assert not camera.supports_batch_update
        if args.debug_outputs:
            output = camera.data.output
            for name in cfg.scene.front_camera.data_types:
                value = output[name].torch
                assert value.shape[:3] == (2, 240, 320), (name, value.shape)
            assert output["rgb"].torch.shape == (2, 240, 320, 3)
            assert output["rgb"].torch.dtype == torch.uint8
            assert output["normals"].torch.shape == (2, 240, 320, 3)
            assert output["normals"].torch.dtype == torch.float32
            assert output["semantic_segmentation"].torch.dtype == torch.uint8
            print("native debug outputs PASS: RGB/RGBA/HDR/albedo/depth/range/normals/segmentation")
        k = camera.data.intrinsic_matrices.torch
        torch.testing.assert_close(k[:, 0, 0], k[:, 1, 1])
        torch.testing.assert_close(k[:, :2, 2], torch.tensor([160.0, 120.0], device=env.device).repeat(2, 1))

        # No physics advancement: place camera 1.2 m in front of a vertical box face.
        robot = env.scene["robot"]
        terrain = env.scene["terrain"]
        tile = terrain.task_tile_to_world[terrain.terrain_levels, terrain.terrain_types]
        state = robot.data.root_state_w.torch.clone()
        state[:, :3] = tile[:, :3, 3] + torch.tensor([1.5, 5.0, 0.5], device=env.device)
        state[:, 3:7] = torch.tensor([0.0, 0.0, 0.0, 1.0], device=env.device)
        state[:, 7:] = 0
        robot.write_root_state_to_sim(state)
        for name in (
            "front_camera",
            "body_height_scanner",
            "fl_height_scanner",
            "fr_height_scanner",
            "rl_height_scanner",
            "rr_height_scanner",
            "terrain_height_scanner",
        ):
            env.scene[name].reset()
        production = read_low_rate_targets(env)
        raw = camera.data.output["distance_to_image_plane"].torch
        near, far = camera.cfg.spawn.clipping_range
        expected_valid = torch.isfinite(raw) & (raw >= near) & (raw <= far)
        assert expected_valid.any(), "current mount should expose visible depth pixels"
        torch.testing.assert_close(production.metadata["depth_valid"], expected_valid)
        torch.testing.assert_close(production.target["depth_image"], torch.where(expected_valid, raw, 0.0))
        calibration = env.scene["calibration_camera"]
        calibration.reset()
        image = calibration.read_sample().values
        print(
            "plane diagnostic",
            "root",
            robot.data.root_pos_w.torch.tolist(),
            "camera",
            camera.data.pos_w.torch.tolist(),
            "optical_quat",
            camera.data.quat_w_ros.torch.tolist(),
            "rawcenter",
            camera.data.output["distance_to_image_plane"].torch[:, 120, 160].tolist(),
            "difficulty",
            terrain.task_difficulty[terrain.terrain_levels, terrain.terrain_types].tolist(),
            flush=True,
        )
        # The separate calibration fixture isolates wall geometry from the robot.
        # Check the analytically projected wall region and require unoccluded samples.
        u = torch.arange(320, device=env.device) + 0.5
        v = torch.arange(240, device=env.device) + 0.5
        wall_y = -(u - 160) * 0.9 / k[0, 0, 0]
        wall_z = 0.55 - (v - 120) * 0.9 / k[0, 1, 1]
        wall = (wall_y.abs()[None, :] < 0.74) & ((wall_z[:, None] > 0.01) & (wall_z[:, None] < 0.59))
        valid_wall = wall[None, :, :] & calibration.read_sample().valid[..., 0]
        print("wall diagnostics", int(valid_wall.sum()), "range", float(image.min()), float(image.max()), flush=True)
        assert int(valid_wall.sum()) >= 100, "insufficient visible known-plane samples"
        torch.testing.assert_close(
            image[..., 0][valid_wall], torch.full_like(image[..., 0][valid_wall], 0.9), rtol=0, atol=2e-4
        )
        print("known plane image-plane depth, centered intrinsics and optical axes PASS")

        # Tilt the robot: foot orientations differ, while every grid must follow base yaw.
        state[:, 3:7] = quat_from_euler_xyz(
            torch.full((2,), 0.3, device=env.device),
            torch.full((2,), 0.4, device=env.device),
            torch.full((2,), 1.0, device=env.device),
        )
        robot.write_root_state_to_sim(state)
        for name in (
            "front_camera",
            "body_height_scanner",
            "fl_height_scanner",
            "fr_height_scanner",
            "rl_height_scanner",
            "rr_height_scanner",
            "terrain_height_scanner",
        ):
            env.scene[name].reset()
        for name in (
            "body_height_scanner",
            "fl_height_scanner",
            "fr_height_scanner",
            "rl_height_scanner",
            "rr_height_scanner",
        ):
            sensor = env.scene[name]
            sample = sensor.read_sample()
            local, _ = sensor.cfg.pattern_cfg.func(sensor.cfg.pattern_cfg, env.device)
            q = state[:, None, 3:7].expand(-1, local.shape[0], -1).reshape(-1, 4)
            offsets = quat_apply_yaw(q, local.repeat(2, 1)).reshape(2, -1, 3)
            ref = sensor.data.pos_w.torch
            starts = sensor.ray_starts_w.torch
            torch.testing.assert_close(starts[..., :2], ref[:, None, :2] + offsets[..., :2], atol=1e-5, rtol=0)
            torch.testing.assert_close(starts[..., 2], (ref[:, 2:3] + 2).expand_as(starts[..., 2]))
            torch.testing.assert_close(
                sensor.ray_directions_w.torch, torch.tensor([0.0, 0.0, -1.0], device=env.device).expand_as(starts)
            )
            valid = sample.valid
            expected_height = ref[:, 2:3] - sensor.data.ray_hits_w.torch[..., 2]
            torch.testing.assert_close(sample.values[valid], expected_height[valid])
            assert torch.count_nonzero(sample.values[~valid]) == 0
        print("base-yaw foot grids, capture-time reference Z, launch offset and no-hit encoding PASS")

        obs, _ = env.reset()
        initial = clone_targets(env)
        calibration_initial = calibration.read_sample().values.clone()
        action = torch.zeros(2, 12, device=env.device)
        for step in range(1, 3):
            obs, *_ = env.step(action)
            torch.testing.assert_close(calibration.read_sample().values, calibration_initial, rtol=0, atol=0)
            for key, value in initial.items():
                torch.testing.assert_close(obs["target"][key], value, rtol=0, atol=0)
            torch.testing.assert_close(
                obs["metadata"]["low_rate_age"], torch.full((2,), step * 0.02, device=env.device), atol=1e-6, rtol=0
            )
        held = clone_targets(env)
        calibration_held = calibration.read_sample().values.clone()
        episode = obs["metadata"]["episode_id"].clone()
        # Native reset renders all camera aliases; row 1 exported storage must stay held.
        env._reset_idx(torch.tensor([0], device=env.device))
        obs = env.observation_manager.compute()
        torch.testing.assert_close(calibration.read_sample().values[1], calibration_held[1], rtol=0, atol=0)
        for key, value in held.items():
            torch.testing.assert_close(obs["target"][key][1], value[1], rtol=0, atol=0)
        assert obs["metadata"]["episode_id"].tolist() == [int(episode[0]) + 1, int(episode[1])]
        torch.testing.assert_close(
            obs["metadata"]["low_rate_age"], torch.tensor([0.0, 0.04], device=env.device), atol=1e-6, rtol=0
        )
        for _ in range(3):
            obs, *_ = env.step(action)
        torch.testing.assert_close(
            obs["metadata"]["low_rate_capture_time"], torch.tensor([0.0, 0.1], device=env.device), atol=1e-6, rtol=0
        )
        critic = env.scene["terrain_height_scanner"].read_sample()
        torch.testing.assert_close(critic.age, torch.zeros(2, device=env.device), atol=1e-6, rtol=0)
        print("T09 PASS: 10 Hz hold, 50 Hz critic, per-row reset identity and renderer-write isolation")
    finally:
        env.close()
