"""Research-only bounded native timing; run with repository .venv Python."""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

import warp as wp
wp.config.enable_backward = False
import gymnasium as gym
import torch
from isaaclab.app import add_launcher_args, launch_simulation
from isaaclab_tasks.utils import resolve_task_config
import r3la.tasks
import r3la.tasks.velocity.mdp.sensor_observations as sensor_obs

parser = argparse.ArgumentParser()
parser.add_argument("--result", required=True)
parser.add_argument("--variant", choices=("baseline", "fused"), default="baseline")
parser.add_argument("--windows", type=int, default=5)
parser.add_argument("--steps", type=int, default=100)
parser.add_argument("--warmup", type=int, default=50)
add_launcher_args(parser)
args = parser.parse_args()
sys.argv = [sys.argv[0]]
if args.variant == "fused":
    from performance_fused_prototype import read_low_rate_targets
    sensor_obs.read_low_rate_targets = read_low_rate_targets
cfg, _ = resolve_task_config("R3la-SWAP-Parkour-UnitreeGo2", "")
cfg.scene.num_envs = 4
cfg.sim.device = args.device
cfg.seed = 7
result = {
    "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "variant": args.variant, "num_envs": 4, "seed": 7, "actions": "zero residual action",
    "warmup": args.warmup, "windows": args.windows, "steps_per_window": args.steps,
    "camera_outputs": cfg.scene.front_camera.data_types,
    "terrain_families": list(cfg.scene.terrain.terrain_generator.sub_terrains),
    "terrain_shape": [cfg.scene.terrain.terrain_generator.num_rows, cfg.scene.terrain.terrain_generator.num_cols],
    "gpu": torch.cuda.get_device_name(), "torch": torch.__version__,
}

def save():
    Path(args.result).write_text(json.dumps(result, indent=2))

def sync():
    torch.cuda.synchronize()

def stats(values):
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    return {"count": len(values), "mean_ms": statistics.mean(values),
            "median_ms": statistics.median(values), "p95_ms": ordered[min(len(ordered)-1, int(.95*len(ordered)))]}

with launch_simulation(cfg, args):
    env = gym.make("R3la-SWAP-Parkour-UnitreeGo2", cfg=cfg).unwrapped
    try:
        with torch.inference_mode():
            env.reset(seed=7)
            action = torch.zeros((4, 12), device=env.device)
            for _ in range(args.warmup):
                env.step(action)
            sync()
            result["peak_allocated_mib"] = torch.cuda.max_memory_allocated() / 2**20
            result["terrain_types"] = env.scene.terrain.terrain_types.tolist()
            print("BENCH warmup complete", flush=True)
            # Acceptance baseline: no interior hooks/sync, full consecutive step windows.
            full_windows = []
            for window in range(args.windows):
                sync()
                begin = time.perf_counter()
                for _ in range(args.steps):
                    env.step(action)
                sync()
                full_windows.append((time.perf_counter()-begin)*1000/args.steps)
                print("BENCH full-step", window, full_windows[-1], flush=True)
                result["step_windows_ms"] = full_windows
                result["step_median_ms"] = statistics.median(full_windows)
                save()

            # Observation baseline: time actual manager execution inside real steps.
            # Kept separate from full-step baseline to avoid interior sync contamination.
            original_compute = env.observation_manager.compute
            observation_times = []
            def timed_compute(*a, **kw):
                sync()
                begin = time.perf_counter()
                out = original_compute(*a, **kw)
                sync()
                observation_times.append((time.perf_counter()-begin)*1000)
                return out
            env.observation_manager.compute = timed_compute
            obs_windows, categorized = [], {"capture": [], "hold": [], "reset": []}
            camera = env.scene["front_camera"]
            for window in range(args.windows):
                begin_index = len(observation_times)
                for _ in range(args.steps):
                    before_time = camera._capture_time.clone()
                    before_episode = camera._episode_id.clone()
                    env.step(action)
                    reset = not torch.equal(before_episode, camera._episode_id)
                    capture = not torch.equal(before_time, camera._capture_time)
                    categorized["reset" if reset else "capture" if capture else "hold"].append(observation_times[-1])
                obs_windows.append(statistics.mean(observation_times[begin_index:]))
                result["observation_windows_ms"] = obs_windows
                result["observation_median_ms"] = statistics.median(obs_windows)
                result["observation_categories"] = {k: stats(v) for k,v in categorized.items()}
                save()
                print("BENCH observations", window, obs_windows[-1], flush=True)
            env.observation_manager.compute = original_compute

            # Diagnostic only: wall-clock shares inside the observation manager.
            original_read = sensor_obs.read_low_rate_targets
            bundle_times = []
            def timed_read(*a, **kw):
                begin = time.perf_counter()
                out = original_read(*a, **kw)
                bundle_times.append((time.perf_counter()-begin)*1000)
                return out
            sensor_obs.read_low_rate_targets = timed_read
            observation_times.clear()
            env.observation_manager.compute = timed_compute
            for _ in range(30):
                env.step(action)
            env.observation_manager.compute = original_compute
            sensor_obs.read_low_rate_targets = original_read
            result["diagnostic_bundle"] = stats(bundle_times)
            result["diagnostic_bundle_calls_per_observation"] = len(bundle_times)/len(observation_times)
            result["diagnostic_bundle_wall_share"] = sum(bundle_times)/sum(observation_times)
            result["diagnostic_observation"] = stats(observation_times)
            # Explicit partial-reset exercise, reported separately from acceptance windows.
            reset_times = []
            for _ in range(5):
                env.step(action)
                sync()
                begin = time.perf_counter()
                env.reset(env_ids=torch.tensor([0], device=env.device))
                sync()
                reset_times.append((time.perf_counter()-begin)*1000)
            result["partial_reset"] = stats(reset_times)
            result["peak_allocated_mib"] = torch.cuda.max_memory_allocated() / 2**20
            result["completed"] = True
            save()
            print("BENCH COMPLETE", json.dumps(result), flush=True)
    finally:
        env.close()
