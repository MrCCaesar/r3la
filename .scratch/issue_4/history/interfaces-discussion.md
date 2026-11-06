# Issue #4 Interfaces — Draft (Specify)

No new public API is approved. This document will define the selected contracts
as design decisions are confirmed; it is not authorization to implement stubs.

## Existing library APIs — evidence only

- ManagerBasedRLEnv / ManagerBasedRLEnvCfg: approved environment family.
- TerrainGenerator / TerrainImporter: candidate existing pipeline; terrain
  function returns meshes and one origin, not task completion metadata.
- ObservationManager: noise/history mechanisms exist; terminal history timing
  requires an explicit downstream contract.

See research.md for inspected source and commit-specific limitations.

## Project contract inventory — pending design choices

| Contract | Information to specify before approval |
| --- | --- |
| Terrain task regions | Terrain type/level identifiers, coordinate transforms, geometric bounds, spawn/landing semantics, units, batched shapes, generation/cache compatibility |
| Attempt outcome | Episode identity, completion/failure flags, precedence, timestamps, reset lifecycle, exactly-once consumption |
| Curriculum statistics | Inputs, units, actual duration, aggregation scope, thresholds, insufficient-sample behavior, update timing |
| Observations | Feature order, shapes, units, frames, history/reset padding, noise ownership, sample identity and sensor age |
| Terminal/AMP data | State fields, frames, terminal masks, pair alignment, reset separation, external dataset compatibility |

For each selected public function/class/config/data contract, record purpose,
inputs/outputs, types/shapes, units, frames, defaults, constraints, error behavior
and compatibility. Undecided items must remain explicit; none is an implicit default.

## Terrain extension compatibility — approved convention / source facts

User approved following local IsaacLab terrain conventions and placing extensions
under src/r3la/labs/terrains. Official SubTerrainBaseCfg.function accepts difficulty
and a sub-terrain configuration and returns (list[trimesh.Trimesh], numpy.ndarray
origin). Generation coordinates cover (0, 0) to (size[0], size[1]), in metres;
the generator subsequently places/transforms the tile. Mesh config classes use
@configclass and inherit SubTerrainBaseCfg; heightfield variants have their own
base/decorator conventions. Source: ../IsaacLab/source/isaaclab/isaaclab/terrains/
sub_terrain_cfg.py and trimesh/mesh_terrains_cfg.py.

Task-region metadata is a proposed additional project contract, not an extra
return value already supported by the official function. Its transport, shapes,
validation and cache behavior remain to specify. Do not silently change the
official generator return signature.

## Approved curriculum semantics (public API names still pending)

Terrain statistics: completed-attempt Boolean success, grouped by terrain family
and difficulty level, last 100 attempts with minimum 20; success rate dimensionless.
Promotion >=0.8 and demotion <=0.3 adjust one level for the completing environment.
Highest-level overflow randomly returns lower; exact sampling policy is proposed
as S7 in design.md. Startup/manual resets do not contribute attempts.

Velocity score: mean over actual attempt duration of
q=(r_linear+0.5*r_yaw)/1.5, with unweighted bounded exponential terms and the
command applying to each physical transition. Score is dimensionless. Include
terminal transition before reset. Remaining aggregation/defaults are proposed S8.

## S7/S8 approved curriculum details

Uniform random lower-level recycling at highest-level promotion; L=1 holds 0.
Per-terrain-family speed upper bound; one fixed sampled command per attempt.
Only attempts >=1 s enter speed batches; each batch has 20 equally weighted q
means. Mean >=0.8 raises speed bound 0.1 m/s; <=0.3 lowers it 0.1 m/s; otherwise
hold. Clear the batch after its decision. New bounds apply on subsequent attempts.
Initial/max bounds and command lower endpoint remain unresolved. No success gate.

## S9/S10 proposed data contracts — not yet approved

N denotes vectorized environment count. Candidate proprio output float tensor
[N,210] = five chronological frames of 42 features; commands float tensor [N,3].
Feature shape/order, reset repetition and downstream composition are in design.md.
Units: angular/joint velocity rad/s; joint position rad; gravity projection and
policy action dimensionless; commands m/s, m/s, rad/s. Frames, feature scaling,
noise amplitudes, dtype/device and exact default offset contract remain to specify.

Candidate terminal data are pre-reset observations plus validity and episode-end
masks, separate from normal post-reset observations. Shape and naming of terminal
container, sensor age, AMP state and episode identity remain unresolved. This is
project-proposed behavior, not a claim that the stock final_obs API already
provides synchronized history or sensor samples.

## S9/S10 clarification

Approved S9 structure: five 42-feature frames in time order, separate commands and
agreed joint/action order. Use native installed history reset behavior. Source
inspection shows reset zeros storage, then first append backfills all five slots
with the first actual new-episode sample; it is not zero-padded output history.

AMP must retain clean pre-reset terminal state. Initial observations, explicit
boundary/validity markers and depth age are approved. Terminal proprio-history
inclusion is not approved; user requested investigation of excluding it. Previous
S10 candidate text above is historical, not an authoritative implementation contract.

## S10 authoritative terminal scope

The user's latest correction supersedes the terminal noisy-proprio export proposal.
No complete terminal proprio history or extra terminal noisy current sample is
required. Retain clean terminal AMP/critic data and explicit valid/end masks,
separate from normal post-reset observations. WM reconstruction uses its actual
selected input instants; environment does not create an additional terminal WM
sample. Exact public container and timeout/latent conventions remain pending.

## S10 final contract amendment — authoritative

User explicitly removed clean terminal AMP/critic retention as well. No extra
terminal observation container is required for any of proprioception, AMP or
critic. Earlier proposed/approved terminal export passages are superseded.
Normal step observations and episode-end/termination/truncation markers remain,
with done rows representing post-reset initial observations. Normal AMP data
support and agreed sensor-age metadata remain. Consumers must respect episode
boundaries; timeout bootstrap behavior is not selected by this amendment.

## S11–S13 proposed parameter ledger

| Field | Semantics / units | Proposed per-sample uniform noise |
| --- | --- | --- |
| base angular velocity | robot base frame, rad/s | [-0.2, 0.2] |
| projected gravity | normalized gravity direction in base frame, dimensionless | [-0.05, 0.05] |
| joint position | actual minus default, rad | [-0.01, 0.01] |
| joint velocity | actual minus default, rad/s | [-1.5, 1.5] |
| previous action | raw previous environment input, before action-term transformation | none |
| command | body-frame velocity targets, m/s and rad/s | none |

Proposed no extra environment proprio clipping/scaling or post-noise gravity
renormalization. Source functions: installed envs/mdp/observations.py; actual
Newton gravity normalization comes from articulation data/shared kernel, not the
observation decorator's units annotation. Current noise values are project defaults,
not verified paper parameters. All proposed values await S11–S13 approval.

## Approved noise and rate ledger — supersedes earlier S13 scan rates

S12 noise ranges in the table above are approved; S11 processing conventions remain
pending. S13 approved rates after user amendment:

| Signal / subsystem | Rate | Period |
| --- | --- | --- |
| Simulation step / contact sensor | 200 Hz | 0.005 s |
| Control / proprio / command / privilege | 50 Hz | 0.02 s |
| Critic terrain height scan | 50 Hz | 0.02 s |
| WM body height scan | 10 Hz | 0.1 s |
| Four WM foot height scans | 10 Hz each | 0.1 s |
| Depth image | 10 Hz | 0.1 s |

Low-rate sensor readings are held between updates. Reading them at 50 Hz does not
imply new physical samples. Capture-phase alignment, age representation and reset
validity must be defined before implementing the final public sensor contract.

## S11 accepted

S11 semantics in design.md and the parameter ledger are now approved, following
user “11. yes”. No changes to accepted S12 noise or amended S13 sensor rates.

## S14–S16 proposed sensor data

| Output | Proposed shape/type | Units / interpretation |
| --- | --- | --- |
| Depth | float32 [N,240,320,1] | metres, image-plane distance |
| Depth validity metadata | bool [N,240,320,1] | true for a valid range return |
| Critic terrain heights | float [N,187] | base Z minus terrain hit Z |
| WM body heights | float [N,286] | base Z minus terrain hit Z |
| Each WM foot heights | float [N,25] | corresponding foot Z minus hit Z |
| Height validity metadata | bool, same shape as corresponding heights | distinguishes no-hit fill from real zero |

All tensors reside on the environment device; exact float dtype for scans remains
to fix (float32 recommended). Preserve existing scan field separation rather than
introducing an implicit new concatenation. Grid geometry and ordering: design.md
S16. Sensor capture time/age are seconds in simulation time; exact shape/keys and
per-environment reset generation identification remain to specify. Invalid sample
metadata is not automatically concatenated into policy/critic/model inputs.

Official image_depth supports channels-last metric output and invalid fill, but
a validity mask and synchronized low-rate bundle are project-proposed contracts,
not a claim of existing automatic library behavior. Defaults for range calibration
and error handling of impossible configuration remain undecided.

## S15/S16 approval

Depth and scan contracts proposed above are approved by user S15/S16 yes.
The S14 low-rate synchronization/initial-validity implementation is still pending
investigation of installed defaults. Equal frequency does not by itself establish
an atomic multi-sensor output contract or correct backend reset freshness.

## Revised S14 approved

User approved native sensor scheduling, update_latest_camera_pose=True and held
output isolation by environment. Exact adapter interfaces and native capture
bookkeeping access remain to specify; partial-reset correctness is unverified.

## S17 proposed clean critic layout

Offsets are half-open [start,end), ordered on last dimension of float32 [N,273].

| Range | Meaning | Units/frame |
| --- | --- | --- |
| [0,8) | thigh flags FL FR RL RR, then calf flags same order | Boolean values encoded as float |
| [8,20) | effective D gains | actuator damping coefficients |
| [20,32) | effective P gains | actuator stiffness coefficients |
| [32,35) | base COM displacement from default | m, base-local frame |
| [35,36) | base mass | kg |
| [36,37) | shared foot restitution | dimensionless |
| [37,38) | shared foot friction | dimensionless |
| [38,41) | base linear velocity | m/s, base frame |
| [41,44) | base angular velocity | rad/s, base frame |
| [44,47) | projected gravity | dimensionless, base frame |
| [47,50) | command | m/s, m/s, rad/s |
| [50,62) | joint position minus default | rad |
| [62,74) | joint velocity minus default | rad/s |
| [74,86) | previous environment input action | dimensionless |
| [86,273) | critic terrain heights | m, S16 scan convention |

P gains have torque/angle units N*m/rad; D gains N*m*s/rad. Contact thresholds,
material combination semantics and randomization cadence remain pending. Public
keys/dtype validation/default configuration are not finalized by this proposed layout.

## S18 proposed action mapping

Input finite float tensor [N,12] on environment device; canonical joint order S9.
Official JointPositionAction: scale=0.5 rad/unit, use_default_offset=True,
preserve_order=True, clip=None. Output is per-joint target position in radians.
Retain backend/asset actuator constraints; this mapping does not certify physically
achievable targets. Shape/device error handling follows the selected official
manager path and will be recorded before interface approval is complete.

## S17/S18 accepted

User approved the proposed [N,273] critic layout and q_default+0.5*a action mapping.
Contact thresholds, material interpretation and randomization remain unapproved
until their dedicated decisions. Official asset defaults are not hardware validation.

## S19/S20 pending physical defaults

Candidate terrain-relative height and Go2 0.4 m target, and >1 N normal-contact
rules with complete control-interval collision detection, are documented in design.md.
No valid terrain hits must remain distinguishable from real terrain height zero.
These proposals are not accepted merely because underlying official APIs exist.

## S19/S20 accepted

Terrain-relative height with nominal 0.4 m target and >1 N normal-force contact
rules are approved. Base/thigh/calf collision history covers four physics steps;
critic contact flags use latest sample. Invalid-height behavior remains pending.
S21/S22 speed/terrain candidate numeric defaults are in design.md and unapproved.

## S21/S22 approved defaults

Initial forward sampling [0,1] m/s; speed upper bound clamped [1,3] m/s; lateral
and yaw commands zero; no forced standing allocation; 20 s max episode duration.
Ten terrain levels and the S22 table of parameter ranges are approved. Exact
sampling endpoints/RNG policy and per-family geometry constraints remain to specify.
S23 landing thresholds and S24 native within-level difficulty sampling are proposed,
not yet implementation contracts.

## S23/S24 approved

Landing confirmation uses strict |roll|<30 degrees AND |pitch|<30 degrees; all
other S23 criteria are accepted. Degrees are human-facing specification units;
implementation conversion to radians must preserve strict comparison. Exactly
30 degrees fails the confirmation predicate. S24 native row-stratified difficulty
sampling is approved. Numerical equality and boundary tests belong in Plan.

S25 stance formula/thresholds and S26 all-invalid-height handling are proposed in
design.md; no silent finite-value fallback is authorized yet.

## S25/S26 accepted

Stance gate uses latest four-foot normal-force norm >1 N, planar command <0.1 m/s
and absolute yaw command <0.1 rad/s; stance exponential uses sqrt(roll^2+pitch^2)
in radians and approved height. All-invalid critic scan sets height penalty/stance
reward to zero and exposes invalid height without adding a reset trigger.
S27 camera calibration and S28 route dimensions remain proposals in design.md.

## S27/S28 approved parameter changes

Simulation camera calibration S27 is approved as provisional project values,
including position, forward view, 87-degree HFOV, 320x240, 0.1–5 m range.
S28 platform amendment is interpreted as box top and stair top each 1.2x1.2 m;
other route/tile/approach values remain. Exact quaternion/intrinsics construction
and geometric placements remain to finalize. S29 margin and S30 unilateral/mirror
geometry are proposed, not automatically implied by platform-size approval.

## S29/S30 current geometry contract

Top platforms: box and stair 1.5x1.5 m; completion base-center bounds inset 0.15 m
on each horizontal edge, yielding 1.2x1.2 m. Supersedes earlier top sizes.
Tilted/mirrored variants only for slopes (0–20 degrees) and stairs (0–15 degrees).
Other terrain types do not gain tilted variants. S31/S32 candidate randomization
and reset parameter values are listed in design.md and remain unapproved.

## S31/S32 approved

Startup material/mass/COM/gain randomization and reset pose/joint ranges are approved
as specified in design.md. User explicitly removed push_robot; no periodic push or
replacement disturbance is in scope. Evaluation randomization choice pending S34.

## S33 candidate AMP fields — Proposed

Named current-state fields, not a concatenated training feature vector: root
position/orientation in world frame; linear/angular velocity in base frame;
absolute joint position/velocity; base-relative foot positions in base frame;
terrain-relative base height plus validity. Shapes, units, order and ownership
are in design.md. Dataset feature selection remains downstream and must not imply
an additional environment terminal snapshot.
