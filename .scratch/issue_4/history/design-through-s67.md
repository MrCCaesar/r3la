# Issue #4 Design — Specify, consolidated draft

## Status and authority

Explore/Research complete; Specify active. S1–S65 (including user amendments and the revised native lifecycle proposal) and user amendments
are approved. Remaining choices P2–P3 are explicitly unapproved; this document is not yet ready for Plan.

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
loader, terminal snapshots or push_robot event. No simulation has been run.

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

Detailed mesh transitions, rock morphology, column distribution and
initial-level distribution are not implied by this table; see P2.

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
implemented learner scope. Environment termination flag choice is proposed in P3.

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

Camera: relative position (0.30,0,0.05) m, looks along base +X, image right=-Y,
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
No independent scheduler. Sample-age/reset-validity remain explicit. Proposed
adapter hooks and ray launch/reach are specified under P1/P2 in interfaces.md.

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
gravity-projection XY². Remaining reward edge conventions appear in P3.

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

## P2 — remaining geometric details, not yet approved

Need decide exact tile placement/gates, ray launch height/reach, slope mesh
tolerance and support-surface membership. Initial levels and family distribution
are approved by S45–S47.
Stair width, gap depth, tilt/difficulty coupling, slope transition surface and
rock-grid construction are approved. Approved
ranges and sizes are not permission to invent these physical details silently.
Geometry/detector contracts are incomplete until P2 is resolved.

## P3 — reward/compatibility conventions approved; table consolidation pending

S55–S58 approve native dt scaling, zero-initialized action histories with immediate
penalties, air-time formula without command gate and native timeout-as-truncation.
No terminal exports or learner bootstrap implementation. Complete reward table and
acceptance coverage still require consolidation against these contracts.

## Verification obligations (not executed)

- All approved shapes, ordering, units, shared-noise identity and reset padding.
- Sensor held-output identity under unrelated resets, capture ages and first-frame
  freshness; valid camera pose/FOV and no self-occlusion; exact grid cardinalities.
- Per-family geometry, mirrored pair correspondence, spawn/region placement,
  cache-on/off metadata agreement and difficulty boundaries.
- Successful passage, airborne crossing, failed landing, within-tile/neighbor bypass,
  permitted leg contact, base collision, timeout, and coincident completion/failure.
- Exactly-once statistics, actual-duration scores, short attempts, simultaneous
  completions, top-level random recycling and no active-attempt command changes.
- Reward formulas, time scaling, missing heights, applied randomization observations,
  state reset isolation, and disabled pushes.
- Registration and bounded headless operation on initial backend. Before any run
  inspect RAM/VRAM; default two environments, serial short runs, no training.

No numerical tolerance or unrun check is claimed passed. Plan/Implement/Verify
remain gated. TODO-01 depth noise, TODO-02 OVPhysX, TODO-03 Isaac Sim PhysX.

## S36/S37 — accepted with S36 amendment

S36: stair width matching the top platform must be configurable, following the
intent of IsaacLab MeshPyramidStairsTerrainCfg.holes. The previous proposal to
force all treads to 1.5 m is superseded. The top remains exactly 1.5 x 1.5 m;
tread run, height range and completion inset remain unchanged. S59 later supersedes
the fixed riser count with dimension-derived count.
S38/S39 below settle the option default and single-flight topology.

S37: single transverse gap has a floor 1.0 m below adjacent approach/landing
surfaces, independent of difficulty. Width remains the approved 0.2–0.8 m range.
Use actual collision geometry (floor and side walls), not an infinite void. Gap
floor is not a valid landing/completion surface. No new reset condition is implied;
base contact and existing failure/timeout criteria remain authoritative.

### S38/S39 — approved

S38: retain the approved +X approach and single ascending flight, borrowing the
holes width behavior rather than adding native four-sided pyramid geometry.
holes=True keeps each tread as wide as the top platform; holes=False allows lower
treads to extend laterally, tapering toward the top. S40 specifies the lateral profile. Missing side steps do not imply a new
infinite pit, gap-depth rule, or reset condition.
S39: use holes=False by default, matching the native configuration; allow True
explicitly. Option remains fixed in terrain configuration, not randomly switched
by curriculum. Approval reference: user “38. yes 39. yes”.

### S40/S41 — approved

S40: for holes=False, define each horizontal tread width from its forward distance
from the near edge of the top platform. Let d_outer (m) be the distance of the
tread's approach-side edge from that platform edge; width=1.5+2*d_outer (m),
centered on the route. Thus successive outward treads of 0.30 m depth gain 0.60 m
in width, following the native square-pyramid lateral envelope. Each tread has a
constant width; this width rule itself does not add treads or longitudinal extent.
The later S59 determines tread count from obstacle dimensions.
holes=True retains 1.5 m width. Route validity stays at the approved 2 m width even
where supporting geometry extends laterally; wider stairs do not authorize bypass.

S41: tilted stairs use the same actual sampled difficulty d for riser height and
transverse tilt: height=0.05+0.18*d m, tilt=15*d degrees. Side slope uses tilt=20*d
degrees without a second superimposed tilt. Apply the approved training orientation
and exact mirrored evaluation geometry. No independent random tilt draw; at fixed
seed/config/d the geometry is reproducible. Box/gap/rocks remain untilted.

Approval reference for S40/S41: user “40. yes 41. yes”.

### S42/S43 — approved

S42: within the approved 2 m side-slope section, reserve 0.5 m entry and 0.5 m
exit transitions, leaving a 1.0 m central constant-cross-slope section. At the
route centerline elevation remains unchanged. Let x range 0..2 m, lateral y
relative to route center; z=y*tan(theta)*a(x), with a=x/0.5 on entry, a=1 in
the middle, a=(2-x)/0.5 on exit. Thus the section connects continuously to level
approach/exit surfaces without adding a vertical ledge. Mirror by y reflection.
This defines the target surface; mesh discretization/error tolerance remains open.

S43: rock patch represented initially by contiguous square raised cells, not
arbitrary rock meshes: 2 x 2 m patch, 0.20 m cells (10 x 10), each cell height
sampled uniformly from [0,h(d)], h(d)=0.02+0.18*d m. No deliberate gaps between
cells, flat cell tops, vertical risers; outside patch level approach/exit. Heights
fixed per generated tile and preserved by caching. This is an approved rough-grid
approximation; do not claim natural-rock morphology or paper-exact geometry.

Approval reference for S42/S43: user “42.yes 43.yes” followed by request to inspect
the installed IsaacLab random-grid terrain for compatibility.

### S44 — approved random-grid adaptation

Reuse the upstream box-grid construction approach in a project terrain function,
not the unmodified random_grid_terrain function. Preserve approved exact 2 x 2 m,
10 x 10 cells, positive-only heights U[0,h(d)], no central platform and full 10 x
10 m task-tile approach/exit layout. Permit zero residual border; use the shared
layout seed/height samples for geometry and metadata. Do not patch upstream, use
zero-size platform meshes, or perturb approved cell size to bypass its checks.

Approval reference for S44: user “44. yes”.

### S45/S46 — approved with user amendments

S45: use native TerrainImporterCfg.max_init_terrain_level=5. With ten rows,
initial terrain_levels are sampled uniformly from integer indices 0..5 inclusive.
This limits initialization, not subsequent curriculum promotion (levels 0..9 remain).
Per-row actual sampled difficulty remains d=(row+U[0,1))/10. This supersedes the
all-level-zero proposal. Evaluation retains explicit level selection.

S46: ordered family proportions are box=0.2, gap=0.2, ordinary stairs=0.1,
tilted stairs=0.2, side slope=0.2, rough grid=0.1. Ordinary/tilted stairs remain
separate curriculum buckets; mirrored right-high geometry remains evaluation-only.
Family remains fixed per environment. Use native column/type assignment, retaining
these configuration proportions. Finite environment assignment can have rounding
imbalance. Two-environment smoke checks need not cover all families simultaneously.
Approval reference: user explicitly amended S45/S46 with max initial level 5 and
ordered proportions 0.2,0.2,0.1,0.2,0.2,0.1.

### S47 — approved with user amendment

Use num_rows=10 and num_cols=20. In the approved order (box, gap, ordinary
stairs, tilted stairs, side slope, rough grid), native cumulative-proportion
allocation gives 4,4,2,4,4,2 columns. This realizes terrain-column proportions;
finite environment counts may still have rounding differences. Column count
remains configurable. The previous proposed default of ten columns is superseded.
Approval reference: user “47. 10行 20列”.

### S48/S49 — approved placement and exit regions

S48: in the approved corner-based 10 x 10 m tile frame, center the route at y=5 m
and start each obstacle at x=3 m. Approach rectangle: x in [1,3], y in [4,6] m;
nominal spawn base XY=(2,5) m, yaw=0. Apply approved reset jitter relative to this
pose, with height determined by the approved local-surface rule. Obstacles and
platforms are centered laterally. Existing geometry lengths determine obstacle end;
no scaling to fill the tile. Tile origin remains distinct from spawn. Reject layouts
whose geometry/safe spawn footprint cannot fit; do not silently alter dimensions.

S49: slope and rough-grid traversals each end in a flat 2 x 2 m landing region
immediately after the approved 2 m obstacle section (x=[5,7], y=[4,6] under S48).
Gap retains the approved 2 m far landing length with 2 m route width, starting at
x=3+gap_width. Apply the approved 0.15 m inset to these landing rectangles, giving
1.7 x 1.7 m base-center completion regions. These are at approach ground elevation.
Box/stair completion remains on the approved top platform (1.2 x 1.2 m inset
region), not on a newly added far-side ground landing. All use approved landing
confirmation and failure precedence. Landing length does not extend obstacle length.

Approval reference for S48/S49: user “48. yes 49. yes”.

### S50/S51 — approved traversal predicates

S50: gates are ordered forward crossings by base-center XY trajectory. Use the
segment between consecutive control samples, test x_prev < x_gate <= x_current,
and interpolate y at the crossing. Test against each gate's lateral span; do not
require a sample to land exactly on the gate. Gates are vertical without a height
ceiling, so valid jumps are allowed; target-surface support and finite landing
confirmation still determine completion. Process multiple crossings within a step
in trajectory order. Entrance is at obstacle start, exit is at obstacle end/top
platform near edge as applicable. Gate spans follow the designated traversable
surface, capped by the 2 m legal corridor; exact per-family layout derives spans.
A forward crossing outside its gate span is bypass, not progress. Crossing back
through an already passed gate clears progress for that gate and all later gates,
so a fresh forward traversal is required. Reset sets previous XY to actual spawn
and clears gate progress; it must not create a teleport crossing.

S51: use base-center XY for the task legal corridor. Lateral bounds are y=[4,6];
longitudinal bounds run from x=1 through the far edge of the designated landing
surface (box/stairs: top platform far edge). First sampled exit ends the attempt
as unsuccessful bypass; no grace duration. Moving backward within the corridor
is allowed, subject to S50 progress rollback. Foot positions alone do not trigger
bypass resets. Completion uses its tighter inset region. Bounds are inclusive;
base collision/timeout precedence remains as approved. Sub-control-step lateral
excursions not visible at sampled endpoints are not claimed detected.

Approval reference for S50/S51: user “yes” in response to both numbered questions.

### S52 — approved landing support attribution

Use native terrain-filtered foot contact-point tracking for the four feet. A foot
supports the target only if its latest upward normal force exceeds 1 N, the native
reported terrain contact position is finite, its XY is within the actual target
landing surface, and its perpendicular distance to that surface is <=0.03 m.
Use full surface bounds for foot support, not the inset base-center completion
rectangle. Inclined stair tops use their actual tilted plane. Existing 0.2 s window,
sample fraction and distinct-foot rules remain unchanged.
Native reported points are aggregates, not exact per-contact patch identity; this
is a bounded approximation requiring edge/wall/mixed-contact verification. Missing
or nonfinite points do not count as support and do not add a reset condition.
If terrain filters/point tracking cannot initialize on a supported backend, fail
setup explicitly; do not silently substitute unconditional foot force checks.
Exact native filter binding/force association requires integration validation.

Approval reference for S52: user “yes” following the contact-position proposal.

### S53/S54 — approved ray bounds and mesh accuracy

S53: all terrain-height grids (critic/body/feet) launch world-down rays from
reference-body world Z + 2.0 m, with max_distance=5.0 m. Keep XY placement/base-yaw
alignment and approved sample rates. Height output remains reference-body Z minus
hit Z; launch offset is not added to reported height. Miss/out-of-range retains
approved zero+invalid representation, no clipping or last-hit reuse. These bounds
are configurable and finite; they do not promise visibility in arbitrary airborne
or out-of-bounds poses. Validate approved terrain/spawn configurations fit intended
coverage; invalid geometry/sensor settings fail setup instead of silent adjustment.

S54: side-slope transition surface is triangulated on a grid with maximum XY
spacing 0.05 m, explicitly including entry/middle/exit break lines. Validate
maximum vertical mesh-to-analytic surface deviation <=0.001 m over each triangle
(using analytic extrema or a conservative bound, not only mesh vertices). Keep
this mesh tolerance separate from S52 0.03 m contact-location tolerance. Planar
box/stair/gap/grid surfaces use direct planar faces; no blanket subdivision.

Approval reference for S53/S54: user “yes” following both questions.

### S55/S56 — approved with S56 amendment

S55: preserve native RewardManager time scaling: reward_step=step_dt*sum_i(w_i*r_i),
step_dt=0.02 s. Reward functions return unscaled terms, configured weights are not
multiplied by 50 to compensate. Ending-step reward is computed before reset as
native. Curriculum q remains the separately approved unweighted tracking score,
not the weighted/time-scaled total reward or normalized reward log.

S56: action-rate uses raw input actions and native reset previous-action=0; first
step penalty is ||a_0||^2 and subsequent values ||a_t-a_(t-1)||^2. Second-order
smoothness uses zero pre-episode actions a_-1=a_-2=0 and is active immediately:
first step ||a_0||^2; second ||a_1-2*a_0||^2; third and later
||a_t-2*a_(t-1)+a_(t-2)||^2. Clear only resetting environments' history; never carry
action differences across episodes. This supersedes the proposed/current-code
first-two-step suppression. Both norms receive configured weights and native dt.
Approval reference: user approved S55 and explicitly amended S56 startup formulas.

### S57/S58 — approved reward/termination conventions

S57: air-time term retains current threshold 0.5 s and weight +0.5; raw term is
sum_feet((last_air_time-0.5)*first_contact). Use native contact timing/first-contact
reporting for each control interval. Remove the stock planar-command-norm>0.1 gate;
do not clamp negative values. A short swing can therefore contribute negatively
on contact, including at low commands. Native dt scaling applies once as in S55.
This proposal does not add extra success bonuses or change stance gating.

S58: retain native termination/truncation distinction. Successful completion,
base collision and bypass are termination terms; 20 s time limit is a time_out=True
term (truncation). Preserve is_finite_horizon=False. If physical failure and timeout
coincide, native terminated and truncated may both be True; do not rewrite them
into mutually exclusive flags. Task success remains False on any coincident
failure or timeout. All boundary types reset and contribute to approved curriculum
statistics when a valid attempt ends. No terminal observation export, extra clean
AMP/critic snapshots or learner/bootstrap changes are introduced. Downstream must
honor boundaries; compatibility with omitted final observations remains a separate
consumer obligation, not an assertion that arbitrary learners are compatible.

Approval reference for S57/S58: user “同意” in response to both questions.

### S59 — approved user amendment: dimension-derived stair count

User rejects a fixed count: compute stair count from obstacle-region dimensions
and tread depth. The top platform does not include the highest stair tread;
reserve its full 1.5 m length separately. This supersedes all earlier fixed-four-
risers and platform-as-fourth-tread proposals, including historical S28/S36/S40
references. Keep 0.30 m tread depth, approved rise range, width/holes behavior and
1.5 x 1.5 m platform. Exact obstacle-region length, remainder handling and relative
platform elevation are not implied by this amendment and remain open.
Approval reference: user S59 explicitly states automatic count and separate platform.

### S60/S61 — user amendments; native geometry reconciliation pending

S60: user directs count calculation to follow IsaacLab pyramid_stairs_terrain.
Reject the previously proposed one-sided floor((L-1.5)/0.30) formula and unapproved
3.9 m budget; retain their history in conversation/status, not as active defaults.
Native formula: N=int(min((Sx-2*b-p)//(2*t)+1,
(Sy-2*b-p)//(2*t)+1)), with platform parameter p, tread depth t, border b.
Its central platform actual dimensions are (Sx-2*b-2*N*t, Sy-2*b-2*N*t), not
necessarily (p,p). Native platform elevation is (N+1)*h; highest tread is N*h.

S61: user rejects equal-height platform. Following native elevation convention
would put the platform one additional rise h above the highest tread; this is the
recommended interpretation, pending reconciliation of native geometry as a whole.
No approved 3.9 m footprint or border value is inferred from this response.

### S62 — approved native residual platform with corrected inset rule

User selects native residual-platform dimensions: platform_width=1.5 m is a
calculation parameter, not an exact physical stair platform size. Apply native
count and actual remaining XY dimensions after removing 2*N*t from usable region.
Platform is separate from highest tread and follows native elevation (N+1)*h,
one rise above that tread. This supersedes exact stair platform 1.5 x 1.5 m and
fixed stair completion 1.2 x 1.2 m in earlier sections; box dimensions are unchanged.

User immediately corrected their initial center-only completion request: use
actual platform boundaries inset by the approved 0.15 m on each edge. For actual
platform dimensions Px,Py, completion dimensions are Px-0.30,Py-0.30 m. Do not
replace this rectangle by a center-point or distance-to-center criterion. If either
result is nonpositive, reject the configuration under the existing invalid-layout
rule; do not silently shrink margin. Foot support uses full actual platform bounds.

S40's fixed 1.5-based width envelope is superseded where incompatible with native
residual geometry. Native holes semantics remain authoritative: holes=True uses
configured platform_width for directional tread span; actual center platform may
be smaller. holes=False uses the native shrinking lateral spans. Preserve the
approved single +X flight, rather than adding four-sided routes.

Approval reference: user chose native residual dimensions, then explicitly corrected
“完成区域也需按实际平台重新内缩，不按实际平台中心确定”. Full stair region dimensions,
border and tilted transform still need explicit resolution; illustrative 10 m /
zero-border arithmetic is not an approved default.

### S63 — user amendment: count from remaining region after entrance

User rejects using full10x10 m tile for stair count. Use the remaining obstacle
region after excluding the entrance/approach area. This supersedes the proposed
15-tread/full-tile result and its3.68 m height; those were never approved defaults.
Retain native count formula, residual-platform rule and separate platform rise.
Approved layout has approach x=[1,3], obstacle entrance x=3, tile x=[0,10]. The
leading x=[0,1] margin is not part of obstacle space. Therefore the natural
post-entrance candidate is x=[3,10], y=[0,10], dimensions7x10 m. Distinguish this
from simply subtracting2 m approach length from10 m (which gives8 m but would
count the leading margin). Exact boundary/border interpretation pending S64.
Approval reference: user S63 explicitly requests remaining space after entrance.

### S64 — approved remaining-region interpretation

Use candidate7x10 m region with border_width=0, p=1.5,t=0.30. Native Nx=10,Ny=15,
N=10; residual platform dimensions Px=1.0,Py=4.0 m. +X ascending flight starts at
x=3, has3.0 m tread run, then platform x=[6,7], y=[3,7]. Platform height=11*h,
maximum2.53 m at d1. Inset rectangle is0.7 x3.7 m; success additionally requires
existing legal2 m corridor, i.e. effective lateral overlap. Do not silently square
the residual platform, change corridor width, or replace native min-axis formula.
Single-flight use of native symmetric count leaves unused space after platform;
using all remaining X length for a single flight would require a different formula.
Approval reference: user “yes” following S64. These are approved default inputs
and derived dimensions; count still recomputes when configuration dimensions change.

S64 resolves earlier footprint/border uncertainty: use the7x10 m post-entrance
region and border0 for the native calculation, while retaining single +X placement.
S65 applies tilt only to intermediate treads; entrance/platform stay horizontal.
S64 dimensions describe their unchanged XY geometry. Foot support uses actual platform,
base completion uses inset AND legal corridor; neither predicate widens the other.

### S65 — approved with horizontal entrance/platform amendment

User keeps the proposed tread shear but requires entrance and platform horizontal.
For stair tread k=1..N only: z_k(x,y)=k*h+(y-5)*tan(theta), theta=15*d degrees;
positive y high in training. Keep XY geometry, native count and holes spans.
Approach remains z=0 throughout, including x=[2.5,3]; no approach transition.
Top platform is horizontal at z=(N+1)*h (default11*h), over the actual residual
platform XY. Completion and support plane use that horizontal platform. Mirror
reflects tread tilt; horizontal entrance/platform remain unchanged.

The proposed all-surface tilt and0.5 m entrance transition are superseded. Interior
tread-to-tread rise remains h at fixed y. Boundary rises are variable:
entrance->first tread h+(y-5)*tan(theta); highest tread->platform
h-(y-5)*tan(theta). These can be negative away from the centerline. Preserve the
specified planes rather than silently clipping heights, changing angles or adding
transition ramps. Mesh construction must not overlay a flat ground collision
surface that masks the prescribed low-side tread; keep entrance outside stair
footprint horizontal and close the stair solids consistently. Final geometry checks
must explicitly cover these boundary joins and negative-relative-height areas.
Approval reference: user “65. 台阶设定保持，但是入口和平台保持水平”.

## S67 — proposed consolidated reward table

User-approved S55–S58 govern timing, startup and airtime. This table freezes all
remaining coefficients/formula choices together; proposal until explicitly approved.
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

## Proposed acceptance coverage for Specify closure

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
| Integration | task registration; reset/step both initial supported backends, eval settings, metadata aliases, native terminated/truncated and wrapper assumptions documented |

Before simulator execution check RAM/VRAM; default headless num_envs2, one bounded
run at a time. Mesh/sensor integration failures require fixing within approved
contracts or an explicit amendment; no lowering acceptance criteria to pass.

S66 final keys/schema in interfaces.md and S67 table/acceptance remain proposed.
After approval, perform final textual consistency consolidation and request explicit
Specify closure/Plan entry. No Plan tasks or production changes are authorized yet.
