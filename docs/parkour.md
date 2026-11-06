# SWAP Go2 parkour environment

Issue #4 supplies the environment and data contracts for downstream SWAP work.
The task ID is `R3la-SWAP-Parkour-UnitreeGo2`. The supported combination is Newton
MJWarp physics with Newton Warp rendering. OVPhysX and Isaac Sim PhysX remain
deferred. No training run, world model, AMP discriminator or motion loader is
included in this delivery.

Use the repository's `.venv/bin/python`. Implementation was checked against
IsaacLab commit `346c74fe722ad371a6c663e3b384b3d172966d11`. Installed distribution
metadata reports `isaaclab 42.0.0`, `isaaclab-newton 11.0.0`, Newton
`1.8.0.dev0`, Warp `1.17.0`, Torch `2.11.0+cu130` and TensorDict `0.14.3`;
the pinned source commit, rather than the package's numerical version, identifies
the inspected IsaacLab APIs.

## Configuration and evaluation

The default generator has ten difficulty rows and twenty family columns:
box/gap/stairs/tilted stairs/side slope/rough grid occupy 4/4/2/4/4/2 columns.
Initial rows are sampled from 0 through 5. Each environment keeps its family;
completed attempts may change its row. Training uses positive transverse tilt.
`PARKOUR_TERRAINS_CFG` is the complete aggregate; the former implementation-era
name `PARKOUR_IMPLEMENTED_TERRAINS_CFG` remains an alias. Terrain configuration
exports under `r3la.labs.terrains.trimesh` use native lazy exports.

After resolving the native simulation presets, apply deterministic evaluation:

```python
from r3la.tasks.velocity.config.Unitree.evaluation import configure_parkour_evaluation

configure_parkour_evaluation(
    cfg, family="tilted_stairs", level=9, velocity=1.0, mirror_sign=-1, seed=7
)
```

The function modifies and returns `cfg`. Family must name one of the six families;
level is integer 0..9, forward velocity is finite 0..3 m/s. Mirroring is supported
only for tilted stairs and side slope. Same seed/family/level reuses canonical
geometry across mirrors. An invalid selection raises `ValueError` before setup.
`make_parkour_evaluation_cfg(...)` also creates an unresolved config; the task
registry exposes it as `eval_env_cfg_entry_point`. Native `play_mode()` uses its
default fixed box/level0/1 m/s settings.

Evaluation uses two environments by default, fixed startup terrain assignment,
nominal joints and dynamics, zero reset jitter, no observation noise and no
curriculum changes. The generator retains difficulty strata so the selected
level refers to its generated row; its `curriculum=True` controls generation,
not adaptive evaluation assignment. A level contains the actual deterministic
sampled difficulty, rather than the exact endpoint `d=1`.

## Returned data and actions

| Group | Shape / contents |
| --- | --- |
| `proprio` | float32 `[N,210]`, five chronological frames of 42 noisy features |
| `commands` | float32 `[N,3]`, current forward/lateral/yaw target |
| `privilege` | float32 `[N,273]`, current clean critic fields |
| `target` | metric depth `[N,240,320,1]`, body heights `[N,286]`, four foot heights `[N,25]` |
| `amp` | named current clean pose, velocity, joints, relative feet, height and height validity |
| `metadata` | episode identity, low-rate capture time/age/alignment and Boolean spatial masks |

The authoritative feature ordering, units and names are in
[interfaces.md](../.scratch/issue_4/interfaces.md). In particular, privilege contains
thigh then calf contact flags, **D then P** gains, COM offset, mass, shared material
values and clean robot/command/critic-scan data. Canonical joint/foot order is
FL, FR, RL, RR. Native quaternions are xyzw; public `amp.base_quat_w` is wxyz.

Actions are finite float32 `[N,12]` on `env.device` in canonical joint order.
Native joint-position targets are `q_default + 0.5 * action`, without action-term
clipping. Call `validate_parkour_actions(env, actions)` at an input boundary when
strict shape/dtype/device/finite validation is required. This optional utility
does not replace native `env.step`; native transfer/broadcast behavior still
applies when callers bypass the check.

Physics steps are .005 s, with four per .02 s policy transition. Proprioception,
critic and AMP data update at 50 Hz; depth/body/foot targets use native 10 Hz
capture clocks. Foot grids follow foot translation and **base yaw**, with
world-down rays from reference Z+2 m, maximum reach5 m. Height is capture-time
reference Z minus terrain Z; no valid-height clipping. No-hit values are zero
with false masks. Invalid critic heights suppress height rewards without
terminating an episode.

The aligned target accessor rejects shape/dtype/device and sample-identity
mismatches. `low_rate_valid` means an aligned capture exists; it does not mean
every ray/pixel hit something. Adapter values/masks/timestamps/episode IDs are
borrowed buffers. They survive unrelated row renders/resets but can change on
their own row's capture/reset. Clone them when retaining transitions. There is
no terminal observation export: returned done-row data belongs to the new episode.

### Production camera mount

The user updated the base-relative mount to `(0.35,0,0.05)` m and confirmed
self-occlusion is resolved. Optical forward remains +X, image right -Y and image
down -Z, with 87 degree horizontal FOV, 320x240 resolution and .1–5 m clipping.
The earlier all-invalid result applied to the old x=.30 m position only.
A separate test-only camera at x=.60 m validates a known wall at .90 m and held
sample isolation. Depth noise remains TODO-01.

## Curricula, rewards and consumers

One native pre-reset curriculum owner keeps per-family/per-level last100 attempt
windows (min20, promote>=.8, demote<=.3), and independent per-family batches of20
attempt tracking scores lasting at least1 s. Speed bounds change by .1 within
[1,3] m/s. Ending rows are processed by ascending environment ID; startup/manual
resets do not count. Statistics survive resets. Commands remain fixed within an
attempt and sample from the updated family bound at the next native reset.
Logs expose `speed_upper_bounds[6]`, window `terrain_attempt_count[6,L]` and
`terrain_success_rate[6,L]`; the count is capped at100, not lifetime attempts.
Float32 duration/score comparisons allow 1e-6 s / 1e-7 numerical boundary error.

All sixteen approved S67 rewards use the native RewardManager's single `dt`
scaling. Base and penalized leg contacts use four physics samples; critic flags
use latest normal force. Airtime has no command gate or nonnegative clamp.
Raw action first/second differences start immediately from zero reset history.
Startup randomization retains applied shared foot friction/restitution, mass,
COM and independent joint gains across episode resets. Evaluation reads nominal
foot materials rather than overwriting them with guessed values. No pushes occur.

The 0.4 m Go2 height reference, mean valid terrain height, 1 N normal-force
threshold and finite landing window are approved project adaptations. They do not
establish exact equivalence to the paper's author implementation or AMP features.

The native RSL-RL wrapper carries nested groups through TensorDict, merges done
flags and forwards `time_outs`. It does not construct terminal critic data or
correct a downstream learner's bootstrap. Existing PPO runner settings remain
outside this environment-only delivery: they refer to a missing `policy` group
and have no world-model input assembler. Do not treat that runner as a runnable
SWAP training implementation. Consumer owners must assemble actor/model inputs
and handle reset boundaries and timeout bootstrap explicitly.

## Bounded implementation checks

Check available RAM/VRAM before simulations. Run serially, headless, two
environments, with bounded durations; no full-scale training is needed.

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_sensors_smoke.py --device cuda:0 --viz none
timeout --kill-after=10s 180s .venv/bin/python tests/parkour_dynamics_smoke.py --device cuda:0 --viz none
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_evaluation_smoke.py --family box --level 9 --wrapper --device cuda:0 --viz none
```

Pytest plugin auto-loading is disabled because an unrelated installed ROS plugin
requires unavailable `lark`. Exact evidence, serial family/mirror commands and
remaining review items are recorded in
[implementation.md](../.scratch/issue_4/implementation.md) and
[verification.md](../.scratch/issue_4/verification.md). These are implementation
checks; final Verify stage entry remains subject to the repository's stage approval.


### Camera debug outputs

The held training camera requires `distance_to_image_plane`, and accepts additional
output types supported by its native Newton Warp renderer. For example:

```python
cfg.scene.front_camera.data_types = ["distance_to_image_plane", "rgb", "normals"]
# After environment initialization/capture:
camera = env.scene["front_camera"]
rgb = camera.data.output["rgb"].torch  # uint8 [N,H,W,3]
normals = camera.data.output["normals"].torch  # float32 [N,H,W,3]
```

Other supported types in the installed renderer are `rgba`, `rgb_hdr`, `albedo`,
`depth`, `distance_to_camera`, `semantic_segmentation`, and `instance_segmentation`.
Segmentation coloring is configured on `renderer_cfg`. These are native debug
buffers: clone frames you retain, since rendering can overwrite them. Only the
image-plane depth is exported through the held, episode-aware training sample;
adding debug outputs does not add policy observations or change its cadence.
Defaults remain depth-only. Unsupported types retain native Camera validation.
For a separate RGB-only debug camera, use native `isaaclab.sensors.CameraCfg`
with `data_types=["rgb"]` and `NewtonWarpRendererCfg`, rather than the training
`HeldDepthCameraCfg`. This change does not add other rendering backends.


### Low-rate observation performance and termination ownership

Low-rate observation selectors validate a fresh six-sensor snapshot and return
only the requested field. The complete `read_low_rate_targets` API remains
available for consumers needing all fields. Fixed-shape alignment comparisons
share one GPU-to-host decision on valid data; failures diagnose the original
error on the same samples. No cross-call cache is used, so same-step resets and
metadata changes are visible immediately. Sensor rates, history and storage
ownership are unchanged.

The single termination state owner lives in `mdp.terminations` and is available
as `mdp.ParkourAttemptState` through native lazy exports. The former `mdp.attempts`
module was removed; direct consumers must use the termination module.

Four-environment performance measurement and its limits are recorded with the
Issue #4 performance verification documents.
