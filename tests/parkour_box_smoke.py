# ruff: noqa: E402
"""Bounded native parkour terrain check. Run explicitly; not part of CPU pytest collection."""

import argparse
import math
import sys

import warp as wp

wp.config.enable_backward = False

import gymnasium as gym
import torch

from isaaclab.app import add_launcher_args, launch_simulation
from isaaclab.managers import CurriculumTermCfg

from isaaclab_tasks.utils import resolve_task_config

import r3la.tasks  # noqa: F401


def capture_outcome(env, env_ids):
    """Test observer at native pre-reset hook; copy flags before term reset."""
    term = env.termination_manager.get_term_cfg("parkour_attempt").func
    if not hasattr(env, "_test_success"):
        env._test_success = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
    env._test_success[env_ids] |= term.success[env_ids]
    if not hasattr(env, "_test_ending_contact_points"):
        env._test_ending_contact_points = torch.full_like(
            env.scene["contact_forces"].data.contact_pos_w.torch, float("nan")
        )
    env._test_ending_contact_points[env_ids] = env.scene["contact_forces"].data.contact_pos_w.torch[env_ids]
    if not hasattr(env, "_test_wall_force"):
        env._test_wall_force = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
    history = env.scene["contact_forces"].data.normal_force_matrix_w_history.torch
    env._test_wall_force[env_ids] |= (history[env_ids, ..., 0].abs() > 1).any(dim=(1, 2, 3))

    return torch.tensor(0.0, device=env.device)


parser = argparse.ArgumentParser()
parser.add_argument("--landing", action="store_true")
parser.add_argument(
    "--family", choices=("box", "gap", "stairs", "tilted_stairs", "side_slope", "rough_grid"), default="box"
)
parser.add_argument("--gap-contacts", action="store_true")
parser.add_argument("--holes", action="store_true")
parser.add_argument("--mirror", action="store_true")
parser.add_argument("--tilt-probes", action="store_true")
parser.add_argument("--slope-probes", action="store_true")
parser.add_argument("--grid-probes", action="store_true")
parser.add_argument("--difficulty", type=float, choices=(0.0, 1.0))
add_launcher_args(parser)
args = parser.parse_args()
sys.argv = [sys.argv[0]]
cfg, _ = resolve_task_config("R3la-SWAP-Parkour-UnitreeGo2", "")
cfg.scene.num_envs = 2
cfg.scene.terrain.terrain_generator.sub_terrains = {
    args.family: cfg.scene.terrain.terrain_generator.sub_terrains[args.family]
}
if args.holes:
    if args.family not in ("stairs", "tilted_stairs"):
        parser.error("--holes requires a stair family")
    cfg.scene.terrain.terrain_generator.sub_terrains[args.family].holes = True
if args.mirror:
    if args.family not in ("tilted_stairs", "side_slope"):
        parser.error("--mirror requires tilted_stairs or side_slope")
    cfg.scene.terrain.terrain_generator.sub_terrains[args.family].mirror_sign = -1
if args.tilt_probes and (args.family != "tilted_stairs" or args.difficulty != 1.0):
    parser.error("--tilt-probes requires --family tilted_stairs --difficulty 1")
if args.slope_probes and args.family != "side_slope":
    parser.error("--slope-probes requires --family side_slope")
if args.grid_probes and args.family != "rough_grid":
    parser.error("--grid-probes requires --family rough_grid")
if args.difficulty is not None:
    cfg.scene.terrain.terrain_generator.difficulty_range = (args.difficulty, args.difficulty)
cfg.scene.terrain.terrain_generator.num_rows = 2
cfg.scene.terrain.terrain_generator.num_cols = 1
cfg.sim.device = args.device
cfg.seed = 7
if args.gap_contacts:
    if args.family != "gap":
        parser.error("--gap-contacts requires --family gap")
    cfg.scene.terrain.terrain_generator.difficulty_range = (1.0, 1.0)
cfg.curriculum.capture_outcome = CurriculumTermCfg(func=capture_outcome)
with launch_simulation(cfg, args):
    env = gym.make("R3la-SWAP-Parkour-UnitreeGo2", cfg=cfg).unwrapped
    try:
        env.reset()
        terrain = env.scene.terrain
        assert 0 < env._parkour_spawn_radius <= 0.8
        assert terrain.task_gates.shape == (2, 1, 1 if args.family == "box" else 2, 3)
        assert terrain.task_family_id.dtype == torch.int64
        assert terrain.task_gate_valid.dtype == torch.bool
        assert terrain.task_difficulty.device == torch.device(env.device)
        if args.family in ("stairs", "tilted_stairs"):
            assert torch.all(terrain.task_tread_count == 10)
            assert terrain.task_tread_bounds.shape == (2, 1, 10, 2, 2)
            assert terrain.task_tread_valid.all()
        if args.family == "side_slope":
            assert terrain.task_slope_valid.all()
            assert terrain.task_slope_break_x.shape == (2, 1, 2)
        if args.family == "rough_grid":
            assert terrain.task_grid_valid.all()
            assert terrain.task_grid_heights.shape == (2, 1, 10, 10)
            initial_grid = terrain.task_grid_heights.clone()
        robot = env.scene["robot"]
        initial = robot.data.root_state_w.clone()
        other = robot.data.joint_pos[1].clone()
        env.reset(env_ids=torch.tensor([0], device=env.device))
        torch.testing.assert_close(robot.data.root_state_w[1], initial[1], rtol=0, atol=0)
        torch.testing.assert_close(robot.data.joint_pos[1], other, rtol=0, atol=0)
        ids = torch.arange(2, device=env.device)
        spawn = terrain.task_spawn_pos[terrain.terrain_levels[ids], terrain.terrain_types[ids]]
        root = robot.data.root_pos_w
        assert torch.all(torch.abs(root[:, :2] - spawn[:, :2]) <= 0.20001)
        torch.testing.assert_close(root[:, 2], spawn[:, 2] + 0.4)
        assert torch.count_nonzero(robot.data.root_vel_w) == 0
        for _ in range(5):
            env.step(torch.zeros((2, 12), device=env.device))
        if args.landing:
            # Controlled placement isolates the approved contact/landing criterion;
            # this is not a policy-performance experiment.
            transform = terrain.task_tile_to_world[terrain.terrain_levels, terrain.terrain_types]
            pose = torch.zeros((2, 7), device=env.device)
            center = terrain.task_support_xy[terrain.terrain_levels, terrain.terrain_types].mean(dim=1)
            pose[:, :3] = transform[:, :3, 3]
            pose[:, :2] += center
            pose[:, 2] += -terrain.task_support_offset[terrain.terrain_levels, terrain.terrain_types] + 0.4
            pose[:, 6] = 1
            # Row 1 is a sideways failed landing with base overlapping the platform.
            pose[1, 2] -= 0.35
            pose[1, 3] = 2**-0.5
            pose[1, 6] = 2**-0.5
            robot.write_root_pose_to_sim(pose)
            robot.write_root_velocity_to_sim(torch.zeros((2, 6), device=env.device))
            robot.write_joint_state_to_sim(
                robot.data.default_joint_pos.torch.clone(), torch.zeros((2, 12), device=env.device)
            )
            success = False
            failed_landing = False
            force_seen = False
            for _step in range(50):
                _, _, terminated, truncated, _ = env.step(torch.zeros((2, 12), device=env.device))
                data = env.scene["contact_forces"].data
                points = data.contact_pos_w.torch
                force_seen |= bool(torch.isfinite(points[0]).any())
                base_done = env.termination_manager.get_term("base_contact")
                if bool(env._test_success[0]):
                    success = True
                if bool(base_done[1]):
                    failed_landing = True
                if success and failed_landing:
                    break
            assert force_seen, "no finite terrain-filtered contact point during real landing"
            assert success, "normal box landing never completed confirmation"
            assert failed_landing, "sideways failed landing did not trigger base collision"
            print(f"{args.family} PASS: real support points, normal landing success and failed sideways landing")
        if args.gap_contacts:
            env.reset()
            env._test_success.zero_()
            env._test_ending_contact_points.fill_(float("nan"))
            env._test_wall_force.zero_()
            transform = terrain.task_tile_to_world[terrain.terrain_levels, terrain.terrain_types]
            gates = terrain.task_gates[terrain.terrain_levels, terrain.terrain_types]
            pose = torch.zeros((2, 7), device=env.device)
            pose[:, :3] = transform[:, :3, 3]
            pose[:, 0] += gates[:, :, 0].mean(dim=1)
            pose[:, 1] += 5
            pose[:, 2] -= 0.6  # Nominal root clearance above the actual z=-1 floor.
            pose[:, 6] = 1
            # Row 1 deliberately touches the far vertical wall below landing height.
            pose[1, 0] = transform[1, 0, 3] + gates[1, 1, 0] - 0.17
            pose[1, 2] = transform[1, 2, 3] - 0.4
            robot.write_root_pose_to_sim(pose)
            robot.write_root_velocity_to_sim(torch.zeros((2, 6), device=env.device))
            robot.write_joint_state_to_sim(
                robot.data.default_joint_pos.torch.clone(), torch.zeros((2, 12), device=env.device)
            )
            feet, _ = env.scene["contact_forces"].find_bodies(
                ["FL_foot", "FR_foot", "RL_foot", "RR_foot"], preserve_order=True
            )
            floor_seen = False
            wall_seen = False
            for _ in range(30):
                env.step(torch.zeros((2, 12), device=env.device))
                data = env.scene["contact_forces"].data
                points = data.contact_pos_w.torch[0, feet, 0]
                force = data.normal_force_matrix_w.torch[0, feet, 0, 2]
                floor_seen |= bool(((points[:, 2] + 1).abs() <= 0.03).logical_and(force > 1).any())
                ending_points = torch.cat(
                    (env._test_ending_contact_points[1, :, 0], data.contact_pos_w.torch[1, :, 0]), dim=0
                )
                wall_seen |= bool(
                    ((ending_points[:, 0] - (transform[1, 0, 3] + gates[1, 1, 0])).abs() <= 0.03)
                    .logical_and(ending_points[:, 2] < -0.05)
                    .any()
                )
                # A wall impact can separate before the final physics substep, so
                # native latest points are absent. Its filtered four-substep normal
                # force history still supplies direct horizontal collision evidence.
                wall_force = data.normal_force_matrix_w_history.torch[1, ..., 0].abs()
                wall_seen |= bool(env._test_wall_force[1] | (wall_force > 1).any())
                assert not env._test_success.any(), "floor/wall contact counted as success"
                if floor_seen and wall_seen:
                    break
            assert floor_seen, "no real supporting floor contact found"
            assert wall_seen, "no real horizontal wall collision found"
            print("gap PASS: actual floor support and horizontal terrain collision; neither attempt succeeds")
        if args.tilt_probes:
            env.reset()
            transforms = terrain.task_tile_to_world[terrain.terrain_levels, terrain.terrain_types]
            sign = terrain.task_mirror_sign[terrain.terrain_levels, terrain.terrain_types].float()
            offset = 0.7 if args.holes else 0.95
            pose = torch.zeros((2, 7), device=env.device)
            pose[:, :3] = transforms[:, :3, 3]
            pose[:, 0] += torch.tensor([3.15, 5.85], device=env.device)
            pose[:, 1] += 5 + sign * torch.tensor([-offset, offset], device=env.device)
            # Keep each probe clear of its surface and within the approved 5 m ray reach.
            pose[:, 2] += torch.tensor([0.23, 2.3], device=env.device) + torch.tensor(
                [-offset, offset], device=env.device
            ) * math.tan(math.radians(15)) + 1.2
            pose[:, 6] = 1.0
            robot.write_root_pose_to_sim(pose)
            robot.write_root_velocity_to_sim(torch.zeros((2, 6), device=env.device))
            env.step(torch.zeros((2, 12), device=env.device))
            hits = env.scene["terrain_height_scanner"].data.ray_hits_w.torch[:, 93]
            local = hits - transforms[:, :3, 3]
            expected = torch.tensor([0.23, 2.3], device=env.device) + sign * (local[:, 1] - 5) * math.tan(
                math.radians(15)
            )
            torch.testing.assert_close(local[:, 2], expected, atol=1e-5, rtol=1e-5)
            if not args.holes:
                assert local[0, 2] < 0, "native collider masks negative low-side tread"
                assert local[1, 2] > 2.53, "native collider altered high-side final tread"
            max_error = float((local[:, 2] - expected).abs().max())
            print(f"tilted_stairs PASS: native low-side/last-tread probes; max_abs_error={max_error:.8g}m")
        if args.slope_probes:
            # Probe the plane and both direct joins, away from ambiguous edge hits.
            maximum_error = 0.0
            for xs in ([3.225, 4.775], [4.0, 2.99], [5.01, 4.5]):
                env.reset()
                transforms = terrain.task_tile_to_world[terrain.terrain_levels, terrain.terrain_types]
                sign = terrain.task_mirror_sign[terrain.terrain_levels, terrain.terrain_types].float()
                pose = torch.zeros((2, 7), device=env.device)
                pose[:, :3] = transforms[:, :3, 3]
                pose[:, 0] += torch.tensor(xs, device=env.device)
                pose[:, 1] += 5 + sign * torch.tensor([-0.775, 0.775], device=env.device)
                pose[:, 2] += 1.5  # World-down launch remains within 5 m of the patch.
                pose[:, 6] = 1.0
                robot.write_root_pose_to_sim(pose)
                robot.write_root_velocity_to_sim(torch.zeros((2, 6), device=env.device))
                env.step(torch.zeros((2, 12), device=env.device))
                hits = env.scene["terrain_height_scanner"].data.ray_hits_w.torch[:, 93]
                local = hits - transforms[:, :3, 3]
                x, y = local[:, 0], local[:, 1]
                envelope = ((x >= 3) & (x <= 5)).float()
                difficulty = terrain.task_difficulty[terrain.terrain_levels, terrain.terrain_types]
                expected = ((y - 5) * sign + 1) * torch.tan(difficulty * math.radians(20)) * envelope
                error = float((local[:, 2] - expected).abs().max())
                maximum_error = max(error, maximum_error)
                assert error <= 0.001, "native slope mesh exceeds approved analytic height tolerance"
            print(f"side_slope PASS: native plane/direct joins; max_abs_error={maximum_error:.8g}m")
        if args.grid_probes:
            maximum_error = 0.0
            for cells in ([(0, 0), (4, 4)], [(4, 5), (5, 4)], [(5, 5), (9, 9)]):
                env.reset()
                torch.testing.assert_close(terrain.task_grid_heights, initial_grid, rtol=0, atol=0)
                levels, columns = terrain.terrain_levels, terrain.terrain_types
                transforms = terrain.task_tile_to_world[levels, columns]
                pose = torch.zeros((2, 7), device=env.device)
                pose[:, :3] = transforms[:, :3, 3]
                for row, (ix, iy) in enumerate(cells):
                    pose[row, 0] += (terrain.task_grid_x_edges[levels[row], columns[row], ix : ix + 2]).mean()
                    pose[row, 1] += (terrain.task_grid_y_edges[levels[row], columns[row], iy : iy + 2]).mean()
                pose[:, 2] += 1.5  # World-down launch remains within 5 m of the patch.
                pose[:, 6] = 1.0
                robot.write_root_pose_to_sim(pose)
                robot.write_root_velocity_to_sim(torch.zeros((2, 6), device=env.device))
                env.step(torch.zeros((2, 12), device=env.device))
                hits = env.scene["terrain_height_scanner"].data.ray_hits_w.torch[:, 93]
                expected = torch.stack(
                    [terrain.task_grid_heights[levels[row], columns[row], ix, iy] for row, (ix, iy) in enumerate(cells)]
                )
                local_z = hits[:, 2] - transforms[:, 2, 3]
                torch.testing.assert_close(local_z, expected, atol=1e-5, rtol=1e-5)
                maximum_error = max(maximum_error, float((local_z - expected).abs().max()))
            print(
                "rough_grid PASS: fixed heights after reset, actual corner/center-cell tops; "
                f"max_abs_error={maximum_error:.8g}m"
            )
        print(f"T01 PASS: radius={env._parkour_spawn_radius:.6f}m; task tensors, partial reset, five steps")
    finally:
        env.close()
