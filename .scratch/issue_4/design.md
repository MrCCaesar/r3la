# Issue #4 Design — Approved, Specify closed

## Status and authority

Explore/Research/Specify complete; decisions S1–S67 are approved with latest user
amendments taking precedence. S66/S67 approval: user “66 yes 67. yes”. This is the
consolidated current specification. Specify closure approved by user “结束 Specify”. Plan entry is authorized; see plan.md (Approved). Prior discussion is preserved under history/, including through-s67 copies.

- Requirements: [requirements.md](requirements.md).
- Primary-source evidence: [research.md](research.md).
- Data/API contracts: [interfaces.md](interfaces.md).
- Decision/approval history: [design discussion](history/design-discussion.md) and
  [interface discussion](history/interfaces-discussion.md). These historical
  proposals are superseded where the current specification differs.
- Accepted ADRs 001–007 record approved major choices; ADR-007 covers revised S35.

Scope: Go2 parkour environment using ManagerBasedRLEnv on inspected IsaacLab
commit `346c74fe722ad371a6c663e3b384b3d172966d11`. Initial backend Newton MJWarp
with Newton Warp rendering. No world-model/AMP networks, training runner, motion
loader, terminal snapshots or push_robot event. At Specify closure no simulation had been run; current implementation evidence is in implementation.md and verification.md.

## Approved terrain and commands

| Item | Current approved value |
| --- | --- |
| Sub-terrain | One obstacle type per 10x10 m tile |
| Route | Local +X forward, 2 m wide approach route, 2 m approach length |
| Box | Height 0.1–0.6 m, top 1.5x1.5 m, complete on top |
| Stairs | Native count/residual-platform rules (S60–S62); tread depth 0.30 m; rise 0.05–0.23 m; platform_width parameter 1.5 m |
| Gap | Width 0.2–0.8 m across route, depth 1.0 m, far landing length 2 m |
| Side slope | Length 2 m, transverse slope 0–20 degrees |
| Rock patch | Length 2 m, protrusion heights 0.02–0.20 m |
| Tilted variants | Slopes and stairs only; stair tilt 0–15 degrees |
| Mirror experiment | Left-high/right-low training; matched reflected slope/stair evaluation |
| Completion inset | 0.15 m per actual platform edge; box region 1.2x1.2 m; stair region uses actual residual dimensions minus 0.30 m per axis |
| Difficulty | 10 rows; native d=(row+U[0,1))/10 sampled on generation |
| Initial command | Uniform forward [0,1] m/s; lateral/yaw zero; no forced standing |
| Command lifecycle | Fixed throughout attempt; heading-command conversion disabled |
| Speed upper bound | Curriculum adjusts within [1,3] m/s |
| Attempt limit | 20 seconds |

Preserve actual sampled difficulty; do not reconstruct it from row index. Geometry
is reused across attempts. Mirror geometry and task-region metadata together using
the same canonical sample. Exact endpoint d=1 may be generated for boundary tests.
Custom terrain functions/classes follow local IsaacLab terrains style and live in
`src/r3la/labs/terrains`; retain `(meshes, origin)` generator return compatibility.
Origin, tile frame and task spawn/landing are distinct concepts.

Exact geometry, initialization and allocation are defined in the consolidated
geometry section below.

## Approved attempt outcome

An attempt must pass the required obstacle through a legal region, enter its
completion region and satisfy a rolling 0.2 s confirmation window (10 control
intervals). During the window:

- Base stays in completion region.
- Strict `abs(roll)<30°` and `abs(pitch)<30°`, world-upright angles.
- `abs(world vertical base velocity)<=0.5 m/s`.
- At least half the control samples have supporting feet; at least two distinct
  feet support sometime in the window; the final sample has support.
- Supporting foot has world-up normal-force component >1 N and supports on the
  intended landing surface. Exact surface membership implementation is in P2.
- No base collision, bypass or timeout. Failure overrides coincident completion.

Region/attitude/vertical-speed violations restart confirmation; inadequate support
delays completion. Four feet need not contact together. Success ends/reset the
attempt. Timeout is unsuccessful. Base collision is the sole illegal-contact
category; thigh/calf contacts incur penalties instead of direct reset.

This finite criterion cannot guarantee indefinite future stability. Legal corridors
must reject within-tile detours while allowing legitimate lateral adjustments;
they are task predicates, not physical walls. Do not add unapproved termination
criteria for foot placement, scans or sensor validity.

## Approved curricula

### Terrain

Pool completed-attempt flags by terrain family and level. Last 100 attempts,
minimum 20: success rate >=0.8 promotes one level; <=0.3 demotes one; otherwise
hold. On promotion beyond highest level, uniformly sample a lower level, excluding
the highest; one-level-only configurations stay at zero. Change only the completing
environment's next assignment. Initial/manual resets do not count.

### Velocity

On every physical control transition compute unweighted
`q=(exp(-||v_cmd_xy-v_base_xy||²/0.15)+0.5*exp(-(yaw_cmd-yaw_rate)²/0.15))/1.5`.
Use the command in force for that transition and include its terminal physics step
internally. Mean over actual duration. No exported terminal observation is needed.

Per terrain family, collect 20 attempts lasting >=1 s, including failures, with
equal weight per attempt. Batch mean >=0.8 increases speed upper bound by 0.1 m/s;
<=0.3 decreases it by 0.1; otherwise hold. Clamp bound to [1,3], clear batch after
decision, apply to subsequent attempts. Never reuse reward logs normalized by
maximum episode time or command metrics finalized after curriculum evaluation.

Completion aggregation order for simultaneous environments is a P1 contract; it
must be deterministic and must not count a sample twice.

## Approved observations, timing and action

| Output | Shape | Semantics |
| --- | --- | --- |
| proprio | [N,210] | Five time-major chronological frames, 42 features each |
| commands | [N,3] | Current velocity command |
| privilege | [N,273] | Current clean critic vector, no history |
| target | Named tensors | Depth, body scan and four foot scans |
| AMP support | Named tensors | Current clean physical fields, not a fixed model vector |
| Metadata | Named fields | Validity, sample time/age, episode boundary information |

No extra terminal noisy, AMP or critic snapshots. Normal done-row observations
belong to the new episode. Runner/model owns input assembly and prevents cross-reset
training pairs; timeout bootstrap compatibility remains explicitly outside the
implemented learner scope. Native termination/truncation behavior is defined in the boundary contract below.

Proprio frame: base angular velocity, projected gravity, default-relative joint
position/velocity, raw previous input action. Canonical leg order FL,FR,RL,RR;
within leg hip-abduction, thigh/hip-pitch, calf/knee. Frames use base +X forward,
+Y left,+Z up. No additional clipping/scaling or post-noise gravity normalization.
Shared additive uniform noise is sampled once: angular velocity ±0.2 rad/s,
gravity ±0.05, joint position ±0.01 rad, joint velocity ±1.5 rad/s. Commands and
actions have no noise. History reset follows native clear then first-sample
backfill; returned initial history repeats one noisy sample five times.

Action `q_target=q_default+0.5*a`, official JointPositionAction, canonical order,
clip=None, nominal official Go2 actuator model/limits. Last action is environment
input before the action-term transform, not necessarily unclipped network output.

Simulation dt=0.005 s; decimation=4; native solver internal substeps remain distinct.
Contact data 200 Hz; proprio/commands/privilege/critic scan 50 Hz; depth/body/four-foot
scans 10 Hz. World-model consumption at 10 Hz is downstream. Five history samples
span 0.08 s from oldest to newest.

## Approved sensor semantics

Camera: relative position (0.35,0,0.05) m, looks along base +X, image right=-Y,
image down=-Z, zero nominal down pitch; valid unit ROS optical rotation. HFOV 87°,
square pixels, centered principal point, 320x240, near/far 0.1/5 m. Depth is metric
image-plane distance, float32 [N,240,320,1]; invalid returns zero plus Boolean mask.
No crop/resize/range normalization or depth noise initially.

Scans: critic 1.6x1.0 m at 0.1 m spacing (187); body 1.05x0.6 m at 0.05 m (286);
each foot 0.2x0.2 m at 0.05 m (25). Center follows respective base/foot XY; all grids
use base yaw, world-vertical rays, official xy flatten order (X fastest). Output
reference base/foot Z minus terrain-hit Z in metres, no ±1 m clipping; no-hit zero
plus separate validity. Sampled reference transform must match sampled ray hits.

Retain native sensor periods, lazy reads and reset invalidation. Explicitly enable
moving-camera pose updates. Hold owned exported samples per environment so
Newton's whole-buffer renders cannot silently overwrite unrelated rows' held data.
No independent scheduler. Sample-age/reset-validity remain explicit. Approved
adapter hooks are in interfaces.md; ray bounds are in consolidated geometry.

## Approved rewards and randomization

Height for stance/height penalty is base world Z minus mean valid critic-hit Z;
nominal target 0.4 m. All-invalid scan yields zero height-related reward contribution
and an invalid-height flag; no zero-ground or stale-height substitution, no reset.

Stance gate: all four feet latest normal-force norm >1 N, planar command norm
<0.1 m/s and abs(yaw command)<0.1 rad/s. Reward
`I*exp(-abs(h-0.4)/0.1)*exp(-sqrt(roll²+pitch²)/0.1)`, weight 1.

Base illegal contact and thigh/calf collision penalties use >1 N normal-force norm
with history covering all four physics steps per control interval; per-link penalty
counts once. Critic flags use latest sample. Stumble uses total-force horizontal/
vertical ratio, separately. Paper roll²+pitch² must not be replaced silently by
gravity-projection XY². The complete approved reward table follows below.

Startup per-environment randomization (retained across resets): shared foot friction
U[0.4,1.2], restitution U[0,0.1], mass log-uniform multiplier [0.9,1.1], COM offsets
x/y ±0.05 m, z ±0.01 m, independent per-joint P/D multipliers U[0.8,1.2]. Critic
reads applied values. Newton uses one friction coefficient. Nominal physical motor
limits are retained, not randomized.

Reset around a safe approach point: XY ±0.2 m, yaw ±0.1 rad, roll/pitch zero,
base velocities zero, joints nominal times U[0.9,1.1], joint velocities zero,
root height local ground+0.4 m. New terrain assignment precedes reset pose selection.
No push_robot or substitute impulse/force event. Invalid spawn geometry must be
rejected rather than silently clipping samples.

## Approved AMP and evaluation (S33/S34)

Current clean named AMP fields: base world position/orientation; base-frame linear/
angular velocity; absolute joint positions/velocities; base-frame foot positions
relative to base; terrain-relative height and validity. No AMP history, terminal
retention, discriminator, dataset loader or assertion of author feature equivalence.

Deterministic evaluation: fixed family/level/command, curricula off, nominal dynamics,
no observation noise or reset jitter, nominal pose/zero velocity. Retain physics,
actions, sensors, rewards and success/failure definitions. Matched mirror pairs
reuse canonical geometry. Randomized robustness evaluation is separate work.

## P1 / S35 — approved implementation seams (revised proposal)

Use project subclasses at existing generator/importer and sensor extension points;
retain upstream code and ManagerBasedRLEnv step/reset loop. See ADR-007 and exact
contracts in interfaces.md. Responsibilities:

1. Terrain generator captures actual sampled difficulty and produces a shared
   deterministic layout used by geometry and task metadata; importer exposes it.
2. Camera copies only legitimately captured rows immediately inside its capture
   hook. Height scanner composes reference-body translation with base yaw.
3. A native stateful termination term owns task progress, landing and pre-reset
   score accumulation. A native stateful curriculum term reads ending rows at the
   existing pre-reset hook and retains statistical windows across resets. No
   finalized-record queue, consumed flags or duplicate episode scheduler.
4. A minimal CommandTerm adds per-family sampling using native reset/countdown;
   its period exceeds the episode limit, keeping commands fixed. Observation
   accessors expose canonical noisy data, clean privilege, target and AMP fields.

Private hook dependence is confined and pinned to inspected source; later upgrades
require compatibility tests. No new custom environment loop or training code.

## Approved consolidated geometry and task regions (S36–S65)

Tile10x10 m, route +X centered at y5; approach x[1,3],y[4,6], nominal spawn ground
reference(2,5,0), yaw0. Root reset adds approved0.4 m clearance and jitter. Obstacle
entrance x3. All geometry/regions are reflected together for matched mirror cases.

Terrain grid10 rows x20 columns; initial max_init_terrain_level5 samples rows0..5
inclusive. Ordered family proportions: box.2,gap.2,stairs.1,tilted_stairs.2,
side_slope.2,rough_grid.1, giving columns4,4,2,4,4,2. Family stays fixed per env;
finite environment counts may have rounding imbalance. Ordinary/tilted stair
curriculum buckets are separate; right-high mirrors are evaluation-only.

Box: height0.1+0.5*d, top1.5x1.5 m, x[3,4.5],y[4.25,5.75].
Gap: width0.2+0.6*d, floor1 m below approach, actual floor/sidewall collision;
far landing starts x=3+width, length2 m,width2 m. Floor is not target support.
Slope/grid obstacle occupies x[3,5],y[4,6], followed by flat landing x[5,7],y[4,6].
All ground landing surfaces are at approach elevation. No extra obstacles per tile.

Stairs: count from remaining7x10 m region,border b=0,parameter p=1.5,tread depth
t=0.30 (m). N=int(min((Sx-2*b-p)//(2*t)+1,(Sy-2*b-p)//(2*t)+1)). Actual platform
Px=Sx-2*b-2*N*t,Py=Sy-2*b-2*N*t. Defaults N10,platform1x4 m. Single +X flight
starts x3, each tread spans0.30 m; platform x[6,7],y[3,7]. Rise h=0.05+0.18*d;
tread k center height k*h, platform(N+1)*h (max2.53 m at d1). No fixed-count or
exact-physical1.5 m stair-platform contract survives S59–S64. Config changes
recompute count/regions; reject invalid/empty geometry without silent clipping.

holes=False default: native lateral tread spans shrink with k (zero-indexed span
Sy-2*b-2*k*t), centered at y5. holes=True uses parameter p as tread span; actual
platform uses p as its Y span too; only its X length uses the residual dimension. Preserve single flight, not four-sided
routes. Earlier S40 fixed1.5-based width envelope is superseded.

Tilted stairs only: tread k plane z=k*h+(y-5)*tan(15*d degrees). Approach z0 and
platform z=(N+1)*h remain horizontal, no entrance ramp. Interior rise stays h;
first/final rises vary laterally and may change sign. Keep specified tread planes;
close meshes without a ground overlay masking low-side geometry. Mirror reverses
transverse sign; XY dimensions and completion stay unchanged. Validate joins.

Side slope (user correction 2026-11-06, ADR-008): theta=20*d degrees;
z=(y-4)*tan(theta) throughout x[3,5], y[4,6] for the canonical sign;
the mirrored surface is z=(6-y)*tan(theta). The lowest edge is at ground z=0,
as requested by the user on 2026-11-06; angle and direct joins are unchanged.
No longitudinal transition ramps: direct vertical joins to surrounding flat ground.
Two top triangles describe the plane exactly; break_x contains only [3,5].
No separate superimposed tilt. Rough grid:2x2 m,10x10 cells of0.20 m; independent
U[0,0.02+0.18*d] heights, flat tops, no deliberate gaps, no center platform. Use
local adaptation of native box-grid construction; exact tiling is valid. Cache
and metadata reuse the same deterministic samples. Boxes/gaps/grid stay untilted.

Completion: actual target rectangle inset0.15 m on each edge. Box1.2x1.2 m;
stairs0.7x3.7 m at defaults; ground landing1.7x1.7 m. Success also requires legal
corridor y[4,6], x from1 through landing far edge. No center-only criterion.
Foot support uses full actual target rectangle, not the base inset. Reject empty
insets or empty completion/corridor intersections at setup.

Gates: forward base-center segment crossing, interpolate y, process ordered gates
in path order; backward recross clears corresponding/later progress. Outside-span
forward crossings are bypass. Box has entrance gate then top completion; gap,
slope,grid have entry/far-edge gates; stairs entry/platform-near-edge gates. Spans
are designated surface widths intersected with corridor. No height ceiling on
crossing. Reset sets previous XY to actual spawn, creating no fictitious crossing.
First sampled base-center corridor exit is bypass failure; feet alone do not reset.

Target support: latest upward normal force>1 N and finite terrain-filtered native
contact point within full target XY, perpendicular plane distance<=0.03 m. Points
are force-weighted aggregates, so edge/mixed-contact behavior requires validation.
Missing points are non-support, not reset. Unavailable tracking fails setup.
Native control-step contact timing/landing window rules remain in outcome section.

Height rays: reference-body world Z+2 m, world-down, max distance5 m. Height output
is reference Z-hit Z, no launch offset added; misses zero+invalid. Keep approved
sample periods. Bounds configurable; validate resulting geometry coverage.

## S67 — approved consolidated reward table

User-approved S55–S58 govern timing, startup and airtime. This table freezes all
remaining coefficients/formula choices together; approved by user S67.
Each listed raw term receives its weight then common step_dt=0.02 s scaling.
Velocities use base frame, except explicitly named world support geometry.

| Term | Raw value | Weight |
| --- | --- | ---: |
| Linear tracking | exp(-||v_xy-command_xy||²/0.15) | 1.0 |
| Yaw tracking | exp(-(omega_z-command_yaw)²/0.15) | 0.5 |
| Stance | approved S25 gated height/orientation exponentials | 1.0 |
| Foot air time | S57 sum((last_air_time-0.5)*first_contact), no command gate | 0.5 |
| Base height | (terrain-relative base height-0.4)²; zero if all hits invalid | -5.0 |
| Vertical velocity | v_base_z² | -1.0 |
| Roll/pitch angular velocity | omega_base_x²+omega_base_y² | -0.05 |
| Orientation | roll²+pitch², world-upright Euler angles in radians | -0.2 |
| Thigh/calf collision | count links with normal-force norm>1 N in four-substep history | -1.0 |
| Foot stumble | count feet with ||F_world_xy||>4*abs(F_world_z), latest total force | -0.1 |
| Hip abduction | sum four hip joint deviations from defaults squared | -1.0 |
| Joint torque | sum applied joint torques squared | -1e-6 |
| Joint acceleration | sum joint accelerations squared | -5e-7 |
| Mechanical power | sum abs(applied torque*joint velocity) | -1e-6 |
| Action rate | sum raw first action differences squared, zero reset history | -0.01 |
| Action smoothness | sum raw second action differences squared, S56 immediate startup | -0.004 |

No additional termination/success reward is introduced. Joint terms cover canonical
12 joints except explicitly four hips. The table matches current coefficients but
incorporates approved contact, height, orientation, airtime and startup corrections.

## Approved acceptance coverage (not executed)

These are obligations for Plan/Verify, not executed tests. Use deterministic synthetic
fixtures before bounded backend runs; never require training performance to accept
the environment. Configuration/shape/boolean results must match exactly; float32
formula fixtures use atol=1e-5,rtol=1e-5 unless a tighter analytic geometry bound is
specified. Sensor depth accuracy must be checked against known planes/calibration;
no promise that contact aggregate errors satisfy mathematical exactness.

| Coverage | Decisions / required evidence |
| --- | --- |
| Terrain metadata/cache | S1,S24,S35,S36–S65: mesh/layout agreement, cache identity, all six families, mirrors, endpoints d0/d1, invalid configs |
| Traversal and support | ordered/rollback/high-speed gates; no bypass success; airborne entry then valid support; wall/pit/non-target contact rejected; failure/timeout wins |
| Observations | exact shapes/ordering/units; one noisy sample reused; five-frame native fill; no terminal exports; clean AMP and privilege |
| Low-rate sensors | 10 Hz held values, partial-reset isolation/freshness, matched capture identities, masks, base-yaw foot grids; critic50 Hz |
| Curricula | thresholds/minimums/windows/batches, duration>=1 s, ending step included, max-level recycle excludes top, initial0..5, family proportions, no duplicate/manual-reset samples |
| Commands/actions | fixed per attempt, updated bounds affect next reset only, canonical q_default+0.5*a, S56 first three actions and partial reset |
| Rewards/randomization | S67 numeric fixtures, no low-command airtime gate, dt once, actual applied randomized values, no pushes |
| Integration | task registration; reset/step the initial supported physics/renderer combination, eval settings, metadata aliases, native terminated/truncated and wrapper assumptions documented |

Before simulator execution check RAM/VRAM; default headless num_envs2, one bounded
run at a time. Mesh/sensor integration failures require fixing within approved
contracts or an explicit amendment; no lowering acceptance criteria to pass.

## Approved reward startup and episode boundary conventions (S55–S58)

RewardManager applies dt once after weighting. Raw action histories reset to zero:
first-order initial penalty||a0||²; second-order starts immediately with||a0||²,
then||a1-2*a0||², then ordinary second difference. Clear selected rows only.
Air-time uses native first-contact timing with0.5 s threshold, no command gate or
nonnegative clamp. No extra success/termination reward.

Successful completion, base collision and bypass are terminated; time limit is
truncated via time_out=True. Both may be true on coincident failure/timeout;
success remains false. is_finite_horizon=False,compute_final_obs=False. No extra
terminal AMP/critic/proprio export. Consumer bootstrap compatibility remains an
explicit downstream obligation, not an implemented learner change.

## Remaining verification risks and handoff

No open design-choice questions remain after S66/S67 and this consolidation.
Runtime verification remains required: Newton contact filters/aggregated locations,
private sensor hooks and partial reset freshness, cache/geometry matching, terrain
joins and scan coverage, wrapper compatibility. No runtime success is claimed.
TODO-01 depth noise; TODO-02 OVPhysX; TODO-03 Isaac Sim PhysX. Approved scope contains
no training runner/model implementation and no push disturbance.

Plan is now active; see plan.md for the proposed breakdown. Production implementation
requires separate approval.


## Camera debug-output extension — 2026-11-06

User requested RGB and other camera output types for debugging. HeldDepthCamera
now accepts additional native Newton Warp output types alongside the required
distance_to_image_plane. Native Camera owns output allocation/type validation;
extras are read via camera.data.output with native buffer lifetime, and must be
cloned for retention. The held SensorSample and training observations still
contain only metric image-plane depth with existing masks/cadence/episode rules.
Defaults remain depth-only; RGB-only debug cameras use native CameraCfg. No
backend or calibration/mount change is included. Examples: docs/parkour.md.

## Approved metadata removal amendment (2026-11-06)

User explicitly requested removing unnecessary metadata exports and consistency
checks after PPO source investigation. ADR-010 supersedes earlier metadata export
and cross-sensor validation contracts in this document. Returned groups are now
proprio, commands, privilege, target and amp. MetadataCfg, sensor_metadata,
LowRateTargets and read_low_rate_targets are removed without compatibility aliases.
low_rate_target(env, key: str) -> torch.Tensor returns the selected native sensor's
borrowed held values with existing shapes/units/frames/dtypes, without checking
other sensors. Unknown keys raise KeyError; native read errors propagate. Retained
values must still be cloned by consumers. Internal sensor sample metadata, native
scheduling, held storage, invalid-value encoding and AMP validity remain unchanged.
