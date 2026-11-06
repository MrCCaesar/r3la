# Issue #4 Design — Draft (Specify)

## Authority and confirmed facts

User approved entering Specify: “准进入 Specify”. Approved requirements and
research evidence are in requirements.md and research.md. Stage approval does
not accept the recommendations below. No implementation or Plan authorization.

## Proposed responsibility boundaries

| Responsibility | Proposed scope | Requirements |
| --- | --- | --- |
| Terrain geometry and task regions | Generate obstacle terrain and consistent entry, valid traversal, landing/completion regions; mirrored counterparts | R9, R12, R15, R19 |
| Attempt outcome | Track traversal and landing evidence; resolve success/failure and expose one result per completed attempt | R10, R13–R16, R18 |
| Curriculum evaluation | Consume actual completed attempts before reset; separate traversal-success and velocity-tracking statistics | R11, R20 |
| Observation production | One shared noisy history, clean privilege, shared depth and reconstruction scans; explicit terminal/reset timing | R4, R22–R24 |
| AMP state export | Supply approved clean state/transition data without training code | R21 |

These are responsibilities, not selected classes or module/file boundaries.

## First design decisions — Approved

S1 / ADR-001: Keep official terrain generator/importer pipeline. Reuse stock
primitive geometry where it matches approved tasks; use project terrain functions
for missing directed/tilted/rock geometry. Define task-local forward +X and
separate spawn/entry, traversal and completion regions rather than equating the
library's origin with successful passage. Box completion may be on the top
landing surface; it must not silently require climbing down. Exact per-type
route and regions remain subsequent decisions.

S2 / ADR-002: Initial support and verification target is the current Newton
MJWarp physics with Newton Warp rendering. Existing alternative presets are not
promised as verified task support. Resolve runtime compatibility through approved
bounded checks; any backend change requires updating the decision and dependent
physics/sensor contracts.

## Assumptions — unverified

- Task-region metadata can be maintained alongside generated terrain without
  modifying upstream IsaacLab.
- Existing Newton combination can meet required contact/material/depth behavior;
  source inspection supports investigation, not runtime certification.

## Open choices and dependencies

After S1: choose each terrain's exact traversal/landing geometry, bypass rules,
mirroring and Go2 difficulty ranges, then measurable success detector conditions.
After S2: finalize force/material/sensor semantics and physical randomization.
Independent upcoming choices: curriculum aggregation and metrics; shared
observation/history and terminal transition contract; reward mapping and AMP data.
All numerical defaults and API names remain unapproved until explicitly recorded.

## Acceptance drafting

Carry research.md's candidate verification coverage forward. Specify must produce
measurable criteria for each approved requirement, including finite-window landing
limitations, before Plan begins. No tests have run in this stage.

## S1/S2 approval additions

Custom terrain functions/classes follow the installed IsaacLab terrains conventions
and live under src/r3la/labs/terrains. See accepted ADR-001.
Newton MJWarp + Newton Warp is the initial support target, not a completed runtime
verification. OVPhysX (TODO-02) and isaacsim_physx (TODO-03) are deferred. See ADR-002.

## Next design choices — Proposed

S3: Task-local +X routes: box from ground approach to box-top completion zone;
stairs from foot of staircase to top platform; gap across one transverse ditch
to far-side landing; lateral slope and rock patch from entry to far-side exit.
Tilted/mirrored variants retain the corresponding route semantics. Completion
is inside a usable support region, not merely at its leading edge. This defines
initial obstacle task geometry; it does not assert exact author mesh reproduction.

S4: Use ordered traversal within a legal region followed by finite landing
confirmation: base in completion region, evidence of supporting foot contact and
acceptable base attitude/vertical motion, maintained over a short interval with
no failure. Do not require all four feet down simultaneously. Base collision,
bypass and timeout override completion on coincident steps. Exact contact
aggregation, thresholds, interval and geometric margins remain next decisions.
Finite confirmation cannot guarantee no later fall; this is an explicit approximation.

## S3/S4 resolutions — Approved

Approval reference: user “3. yes 4. yes”. The S3/S4 proposals above are accepted
at the stated structural level. Per-family routes/completion regions and ordered
traversal plus finite landing confirmation are approved. No numeric landing
threshold, contact aggregation rule or geometry dimension is approved yet.
Base collision, bypass and timeout take precedence over coincident completion.
See ADR-003 for the accepted physical approximation and trade-offs.

## Curriculum proposal — S5/S6, unapproved

S5: Maintain a rolling window of completed-attempt success flags for each terrain
family and difficulty level, pooled across environments in that cell. On a genuine
attempt completion, record the result once; use the resulting cell rate to select
the next level for the completing environment. Candidate initial values: window
100 attempts, minimum 20 samples, promote one level at rate >=0.8, demote one at
rate <=0.3, otherwise hold. Clip to available level range (hold at hardest level),
rather than adopting the stock importer's random recycling above maximum. Initial
and administrative resets are excluded. Other active environments are not migrated
mid-attempt. These are engineering starting values, not paper-reported values.

S6: Track a bounded velocity score on each physical transition before reset, using
the command in force for that transition. Candidate q = (r_linear + 0.5*r_yaw)/1.5,
where the two r values are unweighted exponential tracking terms. This includes
zero-target lateral/yaw tracking as well as forward tracking. Average q over actual
attempt duration; omit unrelated rewards and RewardManager weighting/dt scaling
from per-step q. Do not substitute maximum episode duration or post-reset command
metrics. This is a proposed project metric, not a reported paper curriculum formula.
Aggregation across attempts, speed-range update magnitude/thresholds and minimum
usable duration remain undecided. Short-failure handling must not silently add a
traversal-success prerequisite to the speed curriculum.

## Parameter status

S5's candidate numeric values are awaiting explicit approval and have no convergence
validation. Accepted initial defaults would remain configurable and require later
bounded correctness tests; changing approved behavior requires documented review.

## S5/S6 resolutions — Approved with S5 amendment

Approval reference: user “5. 同意，但是修改达到最高等级后随机退回低等级 6. yes”.

S5 rolling success statistics by terrain family/level, window 100, minimum 20,
promotion >=0.8 and demotion <=0.3, one-level ordinary changes, and completion-only
updates are approved. The previous highest-level hold proposal is superseded:
when progression beyond the highest level is requested, randomly return to a
lower level. Exact lower-level sampling distribution remains S7 below; this
interpretation preserves an opportunity to attempt the highest level rather than
immediately recycling upon first entering it.

S6 actual-attempt mean normalized score (r_linear + 0.5*r_yaw)/1.5 is approved.
No traversal-success gate is implied. Speed-update aggregation and defaults remain
proposed below. Formula and transition timing remain as described in S6.

## Next curriculum choices — S7/S8, Proposed

S7: For L levels numbered 0..L-1, after completing a highest-level attempt whose
cell success rate requests promotion, uniformly sample the next level from
0..L-2. Preserve terrain family; L=1 holds level 0. This excludes the highest
level, unlike the stock random recycling that can choose any row. Demotion from
the highest level still follows the ordinary one-level rule. No recycle merely
because an environment has just arrived at the highest level.

S8: Maintain one shared forward-speed upper bound per terrain family (all levels),
so hard families do not inherit the easier families' speed growth. Completed
attempts contribute their approved mean q if actual duration >=1.0 s; shorter
attempts leave speed statistics unchanged, regardless of outcome. Successful
traversal is not required. Aggregate 20 eligible attempts in a non-overlapping
batch, then mean the per-attempt scores equally. Raise upper bound by 0.1 m/s
if mean >=0.8; reduce by 0.1 m/s if <=0.3; otherwise hold; clear batch after each
update decision. Maintain bounds [initial upper bound, approved maximum upper
bound]; these two speed values remain pending Go2 parameter selection. Changes
apply to commands for subsequent attempts, not active attempts. Hold each attempt's
sampled forward command fixed for its duration. The lower sampling endpoint and
standing-command policy are not selected here. These are engineering proposals,
not paper-reported curriculum parameters.

Known S8 trade-offs: minimum duration avoids unstable one-step scores but excludes
very short valid passes; averaging per attempt weights short eligible attempts
like long ones; per-family bounds add state. A failed long attempt with good
tracking can promote speed, consistent with the approved separate curriculum
basis. Window batching prevents applying repeated speed changes to the same
samples. Future parameter choices must account for these consequences.

## S7/S8 resolutions — Approved

Approval reference: user “7. yes 8. yes”. S7/S8 proposals above are accepted,
including uniform lower-level recycling on highest-level promotion request,
per-family speed bounds, >=1 s eligible attempts, batches of 20 equal-weight
attempt scores, +/-0.1 m/s updates at >=0.8 / <=0.3, next-attempt application,
and holding commands fixed within attempts. Initial/minimum upper bound,
maximum upper bound, lower sampling endpoint and standing policy remain open.

## Observation/transition choices — historical S9/S10 proposals

S9: Canonical noisy proprioceptive frame is [angular velocity (3), projected
 gravity (3), relative joint position (12), relative joint velocity (12), previous
 action (12)], total 42. Use five frames oldest-to-newest, flattened time-major
as [N,210], with current commands separately [N,3]. Each joint-bearing field uses
FL, FR, RL, RR leg order and hip/abad, thigh/hip-pitch, calf/knee within a leg,
matching the explicitly ordered action vector. Preserve noise once per sampled
frame; previous action is not corrupted. On reset fill history with the first
new-episode sample repeated five times, rather than stale frames or five noise
resamples. Command is not history-stacked. Runner/model takes a view of current
noisy features for WM proprioception [N,33] including command and excluding
previous action, and reuses this same value for reconstruction targets. Actor
assembles [N,210] history, [N,3] command and external model latent. This does not
select feature scale, noise amplitude, joint offsets or final public key names.

S10: Supply both a correctly aligned pre-reset terminal snapshot and the normal
post-reset initial observation for done environments, with explicit validity and
termination/truncation masks. Terminal proprio history must include the terminal
measurement exactly once; histories must not cross episode boundaries. Depth
keeps its sensor sampling cadence and identifies its actual sample age rather
than implying a fresh image every control step. AMP clean terminal state also
belongs to the ending episode. Runner/model owns masking/sequence assembly.
The exact lifecycle integration mechanism, public keys and optional fields remain
unselected; enabling the current stock compute_final_obs flag alone is insufficient.

## S9/S10 user clarification — accepted parts and pending research

User approved S9's 42 features, five frames, time-major history, separate commands
and joint/action order. Reset history must follow the current installed IsaacLab
default, not a separately invented padding policy. Source inspection below confirms
zeroing on reset followed by first-sample backfill; external first observation is
five copies of the first new-episode sample.

User requested re-evaluation of terminal proprio history and proposed excluding
terminal frames. The earlier S10 proposal requiring terminal history inclusion is
therefore NOT approved. User explicitly approved AMP terminal clean state belonging
to the ending episode, separate reset observation, boundary/validity masks and
sensor-age semantics. Exact terminal proprio data contract awaits targeted research
and user confirmation; do not infer that terminal instantaneous data are forbidden.

## Revised S10 — Superseded terminal-single-frame proposal

Do not append or export a complete terminal proprioceptive history. Instead,
provide one terminal current noisy sample and command separately, for potential
WM final-transition/reconstruction use, alongside terminal clean critic/AMP state,
sensor data with age and valid episode boundary masks. All consumers of that
terminal noisy quantity share the same sample. Normal returned done-row history
is the next episode's native-filled initial history. Runner determines loss masks
and timeout bootstrapping; these training semantics remain outside implementation
scope here but need an explicit compatibility contract. User confirmation pending.

## S10 resolution — current authoritative scope

Approval/correction reference: user “其他yes,但是论文中世界模型的重建目标都是输入时刻的观测，似乎没有保留step后reset前终止时刻的本体观测的意义”.

For this project, WM training samples are the observations actually supplied at
its selected input instants. Do not introduce an additional terminal WM input or
reconstruction target solely to retain the reset-before/step-after state. Export
neither a terminal proprio history nor an extra terminal noisy proprio sample.
The previous proposed extra terminal noisy sample is superseded.

Retain the approved clean terminal AMP state, clean terminal critic state,
new-episode initial observations, boundary/validity masks and sensor-age semantics.
Do not pair reset observations with the ending episode's actions/hidden state.
Runner/model owns episode sequence boundaries and uses valid selected WM input
instants for reconstruction; no additional terminal reconstruction objective is
imposed by this environment contract.

Paper equation (9) reconstructs observations and auxiliary terrain targets at the
same indexed WM time; terrain targets are not all Encoder inputs. The paper does
not prescribe this project's autoreset collection convention. Excluding terminal
WM samples here is the chosen data scope, not a claim that terminal samples could
never be useful. Timeout bootstrap and external latent alignment remain an open
consumer-compatibility decision; do not silently require a terminal WM update.

## S10 final amendment — no additional terminal snapshots

Authority: user “也不需要保留留终止时的干净 AMP／critic 状态，因为AMP的训练和 actor-critic不需要这些内容”.
This explicitly supersedes all earlier S10 requirements for retaining clean
terminal AMP or critic state, including the previous authoritative-scope section.

Current environment output scope: ordinary observations (done rows belong to the
new episode after autoreset), episode-end/termination/truncation and validity
markers, and agreed sensor-age metadata. Do not add a terminal snapshot container
for proprioception, AMP or critic. Normal AMP data support under R21 remains;
this amendment removes terminal-only retention/export, not all AMP observations.

Runner/model owns sequence-boundary masking. It must not train on a fictitious
last-state-to-reset-state transition. Omitting terminal states intentionally omits
AMP pairs that would require them. No claim is made that every AMP/actor-critic
implementation universally requires or forbids terminal snapshots.

Timeout bootstrap behavior remains a training-consumer compatibility question.
Do not silently change finite-horizon semantics, bootstrap rules or add time
observations merely to remove terminal snapshots. This contract does not prevent
using pre-reset outcome/reward evidence internally for approved curriculum and
logging; it removes additional terminal observation retention/export.

## S11–S13 observation conventions — Proposed

S11: Use official base-frame angular velocity (rad/s), base-frame normalized
projected gravity (dimensionless direction, before corruption), joint position
minus authored default (rad), joint velocity minus authored default (rad/s), and
previous input action before action-term scale/default offset (dimensionless).
Frame convention is robot base +X forward, +Y left, +Z up; verify asset mapping
before implementation acceptance. No additional environment-side feature scaling,
standardization or clipping for these proprio terms; downstream model normalization
is outside this issue. Do not re-normalize gravity after adding measurement noise.
Command axes follow body velocity convention; task-local +X remains the traversal
reference and is not conflated with a rotated robot base frame.

S12: Retain current independent additive uniform noise per component on each new
proprio sample: angular velocity +/-0.2 rad/s, projected gravity +/-0.05,
joint position +/-0.01 rad, joint velocity +/-1.5 rad/s. Previous actions and
commands have no noise; clean privilege remains uncorrupted. Consumers share the
same sampled values and history does not resample old frames. These are existing
project values proposed as configurable defaults, not sourced SWAP noise settings.

S13: Retain physics dt=0.005 s (200 Hz) and control decimation=4 (50 Hz). Refresh
proprioception/commands/privilege and terrain scans at control rate; contact sensor
at physics rate; depth at 0.1 s (10 Hz), held between captures with explicit age.
The physics period is the scene simulation step, not a claim that the solver uses
no internal substeps. Five history frames span 0.08 s between oldest/newest samples.
WM consumes at 10 Hz in downstream runner/model, matching the paper's intended
rate; its actual scheduling/reset handling remains a downstream contract. Camera
capture phase/reset freshness and scan/depth timestamp pairing still need explicit
sensor contract. No extra terminal measurement capture is implied.

## S12/S13 resolutions — Approved with scan-rate amendment

Approval reference: user “12. yes 13. yes, body和四足的地形扫描也降低为10Hz”.

S12 noise defaults and sample-reuse behavior are approved. S13 rates are approved
with explicit amendment: body_height_scanner and all four foot height scanners
used as WM reconstruction targets update at 10 Hz, like depth. The separate
critic terrain_height_scanner remains at 50 Hz; proprioception, commands and
privilege are 50 Hz, simulation/contact sensor 200 Hz. WM consumption is 10 Hz.
This supersedes S13's earlier blanket 50 Hz rate for all terrain scans.

Held body/foot scans retain their last samples between sensor updates. Ten-Hz
frequency alone does not establish capture phase or reset synchronization with
depth; timestamp/age and first-valid-sample behavior remain to specify. Current
measurements must not be re-labelled as fresh simply because ObsManager reads them.

S11 was not answered and remains Proposed: frame/relative-value conventions,
raw-action meaning, no extra proprio scaling/clipping and no post-noise gravity
renormalization must not be marked approved based on S12/S13 alone.

## S11 resolution — Approved

Approval reference: user “11. yes”. Base-frame angular velocity/gravity,
default-relative joint position/velocity, raw previous action, no extra proprio
scaling/clipping and no post-noise gravity renormalization are accepted.

## S14–S16 sensor contracts — Proposed

S14: Depth, WM body scan and four WM foot scans share one 10 Hz sampling schedule
per environment, including the same initial sample phase after reset. Capture
low-rate targets from the same simulated state; hold all data and capture-time
reference transforms between updates, with sample time/age and validity exposed.
On reset invalidate previous-episode samples and obtain a fresh initial sample
before presenting it as valid. No extra physical simulation step is introduced
solely to refresh sensors. Camera/backend refresh mechanism remains to specify
and verify. World-model selection happens on those low-rate sample instants;
ordinary 50 Hz callers may read held values with correct age. Resetting some rows
must not shift other environments' sampling clocks.

S15: Keep current depth resolution 320x240, one image-plane-depth channel in metres,
float32 [N,240,320,1]. No frame stacking, crop, extra resize or range normalization
in the environment initially; runner/model can convert layout/normalize later.
Replace nonfinite/nonpositive/no-hit depth with 0 and carry a Boolean per-pixel
validity mask [N,240,320,1] as auxiliary metadata, not an additional image channel.
Input and reconstruction target share the same image/mask. Near/far clipping,
mount pose/FOV and out-of-range behavior remain pending. This resolution is an
existing project choice, not a verified paper value; depth-noise TODO-01 remains.

S16: Retain current regular grid sizes as project-proposed initial values:
critic 1.6x1.0 m at 0.1 m spacing (17x11=187); WM body 1.05x0.6 m at 0.05 m
(22x13=286); each foot 0.2x0.2 m at 0.05 m (5x5=25). Centers follow base XY or
respective foot XY; all grids use base yaw, not individual foot yaw. Rays are
world-vertical, with origins high enough to sample intended terrain; launch offset
is an implementation parameter and must not change reported heights. Report
reference body/foot world Z minus hit world Z, metres, without clipping valid
values to +/-1 m. Use reference transforms from the same sensor capture instant.
Flatten in official grid 'xy' ordering (X varies fastest), with foot ordering
FL,FR,RL,RR; retain separate named foot arrays. Nonfinite/no-hit rays produce 0
plus Boolean validity metadata; true zero height remains distinguishable by mask.
Exact ray reach/offset, public names and camera-relative occlusion assumptions
remain to specify. Dimensions must be verified against generated patterns later.
These are proposed project choices and do not assert undisclosed paper geometry.

## S15/S16 resolutions — Approved; S14 investigation requested

Approval reference: user “14. 貂蝉isaaclab的默认实现方式后确定；15. yes 16. yes”,
interpreted as investigating IsaacLab defaults before deciding S14.
S15 depth metric/layout/validity and S16 grid/frame/height semantics are approved.
Camera calibration/range and ray reach/offset remain open. S14 synchronization
mechanism is not approved; native lifecycle investigation follows in research.md.

## S14 revised proposal — native schedule plus output isolation

Use official sensor update_period=0.1 s, lazy data access and native reset
invalidation rather than a separate scheduler. Enable update_latest_camera_pose
for the body-mounted camera. Align initialization and read low-rate depth/body/foot
sensors through the target output path; retain sample-age/validity semantics.
Because current NewtonWarp can render all pixel rows for a subset-triggered capture,
maintain owned held output snapshots that only update genuinely captured/due rows;
do not expose mutable aliased renderer output as a supposedly held sample.
Exact adapter API and native timestamp/frame access remain to specify. A two-env
partial-reset check is required in later approved verification. This proposal
supersedes assuming that equal periods alone guarantee S14; approval pending.

## Revised S14 resolution — Approved

Approval reference: user “yes” to native scheduling, moving-camera pose refresh
and per-environment held-output isolation. Revised S14 is accepted; no independent
sensor scheduler is introduced. Runtime partial-reset verification remains required.
See ADR-005. This does not restore any terminal observation exports.

## S17/S18 critic and action contracts — Proposed

S17: Current clean critic observation is float32 [N,273], excluding externally
provided WM latent. Fixed field order: thigh/calf contact flags (8), effective
D gains (12), effective P gains (12), base COM offset (3), base mass (1), shared
foot restitution (1), shared foot friction (1), base linear velocity (3), base
angular velocity (3), projected gravity (3), velocity command (3), relative joint
position (12), relative joint velocity (12), last raw action (12), terrain heights
(187). Contact flags use all thighs in FL/FR/RL/RR order then all calves in that
order. Joint vectors follow S9 order. Use existing physical units/base frames and
approved height semantics; no noise, history or extra feature scaling. Contact
force definition/threshold and randomized parameter ranges remain pending.
All 187 height validity bits are auxiliary metadata, not appended to the 273-vector.
WM latent assembly remains downstream; no terminal critic snapshot.

S18: Retain official JointPositionAction with q_target=q_default+0.5*a, a float
[N,12] in S9 joint order, 0.5 rad per action unit, preserve_order=True and default
position offsets. Keep action-term clip=None (no added project hard clipping),
retaining the official Go2 actuator model/limits; a later runner's input clipping
is distinct and outside this task. Last-action observation is the input received
by the environment before this action-term transform, not necessarily unclipped
network output. Nominal asset stiffness/damping and motor limits come from the
inspected UNITREE_GO2_CFG; randomized gains and other physical choices require
separate approval. Action scale is an existing project value, not sourced SWAP data.

## S17/S18 resolutions — Approved

Approval reference: user “17. yes 18. yes”. Clean current critic layout [N,273]
with declared ordering and separate validity metadata is approved. Joint position
action q_target=q_default+0.5*a, canonical ordering, official Go2 actuator limits
and no additional action-term clipping are approved. Normal AMP feature definition,
randomization and contact thresholds remain open; no terminal snapshots added.

## S19/S20 reward/physical semantics — Proposed

S19: Use one terrain-relative height definition for both body-height penalty and
static-stance reward: h = base_world_z - mean(valid critic-scan terrain_hit_z).
Use 0.4 m as configurable Go2 target height initially, matching the authored nominal
root height/current project setting; this is not a measured standing clearance or
paper Apollo value. This avoids world-height penalty changes solely from elevated
terrain, but the local mean blends surfaces at box/stair edges. Prefer this official
scanner-based approach over a new support-surface estimator initially. No valid
rays is an explicit invalid-height condition; fallback/reward handling remains to
specify, not implicit ground z=0.

S20: For base illegal contact and thigh/calf collision-count penalties, reuse
local official normal-contact-force semantics with threshold >1 N and a history
covering all four physics steps of each control step. Exactly one penalty count
per affected link per control step. Current critic contact flags use the latest
physics-sample normal force >1 N (not the whole interval). This differentiates
current-state observation from transient collision detection. Select only base
for illegal contact, thighs/calves for penalty, feet for stance/support. Retain
paper stumble ratio with total force as a separate term. Threshold/history are
explicit numerical adaptations from the idealized paper >0 collision condition;
normal force differs from total force. No claim of exact formula equivalence.

## Formula reconciliation obligations

R3 requires paper-faithful reward terms unless an adaptation is explicitly approved.
Use paper roll^2+pitch^2 for the orientation penalty rather than silently retaining
projected-gravity XY squared. Stance must select four feet rather than all bodies.
Remaining stance orientation norm, low-command thresholds, airtime gating,
height-invalid handling, action-history initialization and reward time scaling
will be specified explicitly; this paragraph does not approve unresolved choices.

## S19/S20 resolutions — Approved

Approval reference: user “19 yes 20. yes”. Consistent height relative to mean valid
critic terrain hits with 0.4 m nominal Go2 target is approved. >1 N normal-force
contact semantics, full four-physics-step collision history and latest-sample
critic contact flags are approved. Invalid-height handling remains unresolved.
See ADR-006; these adaptations are not claimed as exact paper settings.

## S21/S22 speed and geometry defaults — Proposed

S21: Initial forward command uniform range [0,1.0] m/s; terrain-family speed
curriculum adjusts upper bound with approved S8 increments, clipped to [1.0,3.0]
m/s. Lower endpoint stays zero, lateral/yaw targets zero. rel_standing_envs=0:
no separately forced zero-command episodes; very small positive speeds remain
possible from uniform sampling and may time out. Commands fixed within attempt,
heading-command conversion disabled so it cannot replace the specified yaw target.
Keep maximum attempt duration 20 s. These initial/endpoints and duration are
project defaults; 3 m/s is paper-reported curriculum ceiling, not verified Go2
parkour capability. Current explicit 2% standing allocation is not retained.

S22: Candidate Go2 geometry ranges by difficulty: box height 0.1–0.6 m; gap width
0.2–0.8 m; stair step height 0.05–0.23 m; transverse slope angle 0–20 degrees;
rock protrusion heights 0.02–0.20 m; unilateral box/stair/gap tilt 0–15 degrees.
Base-family magnitude and tilt can jointly depend on level; exact coupling remains
open. Preserve ten difficulty rows initially; placement within each level and
initial level distribution remain pending. Stair range matches inspected official
rough terrain example; gap upper bound matches existing project. Other ranges are
engineering proposals, not established hardware limits or paper reproduction.
Per-tile dimensions, approach/landing lengths, box footprint, stair step run/count,
rock morphology/density and slope transition shape remain separate decisions.
Accepting these defaults would not certify attainability; later changes require
recorded approval rather than silently lowering terrain to pass tests.

## S21/S22 resolutions — Approved

Approval reference: user “21. yes 22. yes”. Speed [0,1] initially, adjustable upper
bound [1,3] m/s, no explicitly forced standing episodes, fixed within-attempt
commands, zero lateral/yaw, and 20 s maximum attempt duration are approved.
S22 geometry ranges and ten difficulty levels are approved as configurable project
initial values, not verified limits. Route dimensions and within-level generation
remain unapproved until specified.

## S23/S24 completion and difficulty details — Proposed

S23: After legal obstacle traversal and entry into the completion region, evaluate
a rolling 0.2 s confirmation window (10 control intervals at 50 Hz). Throughout
that window base stays in completion region; |roll|,|pitch| <=45 degrees relative
to world upright and |base world vertical velocity| <=0.5 m/s; no base collision,
bypass or timeout. A supporting foot is one whose latest normal-contact-force
world Z component >1 N. At least half the window's control samples contain one
or more supporting feet, at least two distinct feet support somewhere in the
window, and the current completion sample has support. Four-foot simultaneous
contact is not required; intermittent no-contact samples are allowed. If pose,
velocity or region conditions fail, discard accumulated confirmation and restart;
support insufficiency simply delays confirmation. Any task failure still ends the
attempt immediately with failure precedence. These are configurable, unvalidated
initial detection thresholds, not paper-reported values. Adequate landing-zone
length must be provided for the allowed commanded speed. The detector is a bounded
proxy, not a guarantee of indefinite future stability or exact body-foot containment.

S24: Prefer native TerrainGenerator difficulty stratification within each row:
for level l of L=10 and difficulty_range [0,1], draw d=(l+u)/L with u uniform [0,1)
when generating each tile. Parameters vary linearly over their approved min/max
ranges unless a later per-family geometry contract specifies another mapping.
Terrain is generated once per construction/seed, not regenerated every attempt.
The highest row samples [0.9,1), so random training tiles need not attain exact
configured maxima. Evaluation fixtures can explicitly generate d=0 and d=1 for
boundary verification. Mirrored variants must reuse the same underlying generated
geometry/seed and reflect it, not redraw independent geometry. This retains the
native pipeline and diversity; deterministic one-value-per-level is the alternative.
Tilt coupling remains to specify separately (do not silently couple tilt to every
other parameter just because both have ranges).

## S23/S24 resolutions — Approved with attitude amendment

Approval reference: user “23. 基座姿态，roll,pitch小于30度。其他yes 24. yes”.
S23 is accepted with strict |roll|<30 degrees and |pitch|<30 degrees, replacing
the proposed <=45-degree bounds. Its remaining window, velocity, support and
failure rules are approved. S24 native stratified within-level difficulty sampling
is approved. Ten levels are bins, not ten exact deterministic parameter values.

## S25/S26 remaining reward edge semantics — Proposed

S25: Static stance indicator requires all four actual feet in contact in the latest
physics sample (normal-force norm >1 N), planar command norm <0.1 m/s and absolute
yaw command <0.1 rad/s. Use the approved terrain-relative height error and propose
orientation magnitude sqrt(roll^2+pitch^2), in radians. Stance term is
I_stance * exp(-abs(h-0.4)/0.1) * exp(-sqrt(roll^2+pitch^2)/0.1), weight 1.0.
Here four-foot contact applies only to static-stance reward, not landing success.
Use world-upright roll/pitch as in the orientation penalty. The norm interpretation
and thresholds fill underspecified details and need approval; they are not all
explicitly stated paper values.

S26: When critic terrain scan has no valid hit, height reference is undefined.
Return zero contribution for body-height penalty and static-stance reward on that
step, and expose/log the invalid-height indicator; do not invent ground height 0
or reuse a stale reference. Other reward terms, dynamics and existing termination
rules continue. A missing scan alone adds no reset trigger. Missing rays within
an otherwise valid scan are excluded from its mean as already approved.
Trade-off: a completely invalid scan temporarily removes height shaping. Validity
counts must be checked during verification so widespread invalid data are not
accepted as a functional environment. This is an explicit missing-data policy,
not a guarantee that sensor outputs are always valid.

## S25/S26 resolutions — Approved

Approval reference: user “25. yes 26. yes”. Four-foot static-stance gating,
command thresholds, Euclidean roll/pitch norm and specified exponential formula
are approved. When critic height reference has zero valid hits, height penalty
and stance reward contribute zero with invalidity reported; no new reset condition.
Other rewards and existing failure rules continue. Missing-data frequency must
be checked during verification rather than silently accepting widespread no-hits.

## S27/S28 camera and terrain dimensions — Proposed

S27: In absence of supplied real calibration, use an explicitly provisional Go2
simulation camera: base-relative position (0.30,0,0.05) m, pointing along base +X
with image right toward base -Y and image down toward base -Z, zero nominal down
pitch. Use CameraCfg ROS optical convention and a valid unit rotation derived
from those axes; never retain current zero quaternion. Horizontal FOV 87 degrees,
square pixels (fx=fy) at approved 320x240, centered principal point under official
pixel convention; near/far 0.1/5.0 m. Compute physical camera intrinsics from
these quantities rather than independently choosing incompatible focal/aperture
values. Renderer no-hit/out-of-range output is invalid, filled 0 with approved
mask. Do not force a far-clip saturation value to be treated as a valid hit.
This is a project calibration proposal, not a claimed real Go2 camera or paper
specification. Self-occlusion and mesh clearance must be checked before acceptance.

S28: Retain 10x10 m sub-terrain tiles. Define a 2 m-wide task route, 2 m approach
zone and at least 2 m completion/landing zone where space permits. Box top is
2x2 m and contains its completion region; final geometric safety margins reduce
usable region and must fit S23 confirmation. Stairs: four risers with 0.30 m run
per step and 2 m top platform. Gap spans the full route width and uses a 2 m
far-side landing zone. Lateral slope and rock patch each occupy 2 m forward length,
with approach/exit transitions separate. A legal corridor rejects base-center
bypass of the obstacle; it is a task predicate, not an added physical wall.
No requirement for every foot to remain inside corridor unless later approved.
Exact placement, endpoint margins, tilted transition surfaces and irregular-rock
shape/placement remain subsequent choices. These are proposed controllable test
geometries, not measured Go2 limits or exact author meshes.

## S27/S28 resolutions — Approved with platform-size amendment

Approval reference: user “27. yes 28. 箱顶/阶梯顶部尺寸采用1.2m”.
S27 provisional camera calibration is approved. S28 is adopted with box top and
staircase top platform interpreted as square 1.2x1.2 m surfaces (both horizontal
extents); other proposed dimensions remain as stated. This explicit interpretation
was communicated to the user; correct it if a different width/length was intended.
The earlier 2x2 m box top and 2 m-long stair top are superseded. Task route width
outside the narrower platforms remains 2 m. Actual stair width and transitions
must be defined consistently with the approved top width.

## S29/S30 geometry and mirror details — Proposed

S29: Use a 0.15 m horizontal inward margin from each completion-platform edge for
the base-center confirmation region. A 1.2x1.2 m platform therefore has a 0.9x0.9 m
base-center completion region. This does not require the whole robot to be inside
that region; supporting feet must contact the intended landing surface rather
than an obstacle side or neighboring terrain (detection method to specify).
At 3 m/s a 0.2 s interval spans 0.6 m, so 0.9 m provides geometric room in a simple
constant-forward-speed case; this arithmetic is not a dynamic attainability proof.
For all other landing surfaces, inset their safe surface bounds by the same margin
where geometrically meaningful. Narrow top/obstacle widths determine legal gates;
a broad 2 m approach corridor alone must not permit bypassing a 1.2 m box.

S30: For unilateral tilted variants, define +Y as the higher side (left when
looking forward along local +X). Apply transverse height variation to the box top,
stair treads and both gap takeoff/landing surfaces, with smooth geometric transitions
from/to approach/exit surfaces. Do not rotate gravity or the entire terrain grid.
Mirror by y -> -y with corresponding geometry/route metadata reflection. During
mirror-generalization evaluation, training uses the +Y-high variant and evaluation
uses its matched -Y-high mirror; hold mirrored evaluation variants out of that
training set. Ordinary non-tilted obstacle tasks remain included. Exact transition
profile and tilt/difficulty coupling remain pending. This is a proposed project
geometry definition, not a claim of recovering unreleased author meshes.

## S29/S30 resolutions — Approved with geometry/scope amendments

Approval reference: user “29.同意余量，将箱顶和阶梯顶部平台尺寸修改为1.5x1.5m 30. yes, 但是仅为斜坡和阶梯生成倾斜地形，其他地形不需要”.

Box top and stair top are now 1.5x1.5 m, superseding 1.2x1.2 m. Approved 0.15 m
inward margin yields 1.2x1.2 m base-center completion regions. Target-platform
support requirement is accepted; detection mechanism/vertical tolerance remain open.

Tilted and matched mirrored variants are restricted to slopes and stairs. No
additional tilted box/gap/rock variants. This explicitly supersedes broader R9/S30
scope. Slopes retain their approved transverse slope range 0–20 degrees; tilted
stairs use approved tilt range 0–15 degrees. Do not superimpose a second slope tilt.
Left-high/right-low training and matched mirror evaluation apply to these variants.
Ordinary box, gap and rock tasks remain; do not add unrelated mirrored variants.

## S31/S32 randomization and resets — Proposed

S31: Retain initial startup randomization for foot material/base inertial parameters,
add effective actuator-gain randomization using official ownership-aware APIs:
shared foot friction uniform [0.4,1.2] per environment, shared restitution uniform
[0,0.1]; base mass log-uniform scale [0.9,1.1]; base COM uniform offsets x/y
[-0.05,0.05] m, z[-0.01,0.01] m; each joint P and D gains independently uniform
scale [0.8,1.2] relative to nominal. Sample once per environment at startup and
retain through resets; critic observes actually applied values. Newton single
friction coefficient means no separately sampled dynamic-friction parameter.
Except added gain scale range, these are current project settings; none is verified
as SWAP parameter provenance. Go2 physical bounds remain nominal, not randomized.

S32: Reset within the assigned approach zone, with uniform XY offset +/-0.2 m
about a designated safe spawn point, yaw +/-0.1 rad about route-forward, initial
roll/pitch zero and base linear/angular velocities zero. Reject invalid geometry
configurations that cannot contain the full spawn footprint; do not clip an unsafe
sample into a supposed valid pose. Joint reset uses nominal positions times uniform
[0.9,1.1], zero joint velocities; root height is local spawn surface plus approved
0.4 m. Event order must use the new terrain level/region before constructing pose.
Retain intermittent planar velocity overwrite perturbation uniform [-0.5,0.5] m/s
per component at intervals sampled [10,15] s, only in training; it is an imposed
velocity perturbation, not an impulse-force model. Disable pushes for evaluation;
other evaluation randomization is a separate choice. Remove zero-magnitude force/
torque reset event as a no-op rather than claim a physical disturbance. Values
are project proposals; nominal reset clearance still needs bounded validation.

## S31/S32 resolutions — Approved with push removal

Approval reference: user “31. yes 32. 去除push robot的扰动”.
S31 startup dynamics randomization is approved. S32 reset pose/velocity/joint
settings are retained; remove push_robot entirely rather than only disabling it
for evaluation. No periodic velocity overwrite or substitute force/impulse event
is introduced. Zero-magnitude force/torque reset event remains unnecessary.

## S33/S34 AMP and evaluation scope — Proposed

S33: Export current clean AMP-support data as named physical fields, not an invented
fixed SWAP AMP vector. Candidate fields: base world position [N,3], base orientation
[N,4] wxyz in world frame, base-frame linear/angular velocities [N,3] each, absolute
joint positions/velocities [N,12] each in canonical order, foot positions relative
to base expressed in base frame [N,4,3] in FL/FR/RL/RR order, and approved terrain-
relative base height [N,1] with validity [N,1]. No noise, history or extra terminal
retention. Runner/model selects/transforms/concatenates fields to match its reference
motion dataset and owns pair/sequence masking. This does not assert author AMP
feature equivalence. Units metres/radians/seconds; floats float32 on env device,
validity Boolean. Ordinary physics data can be read independently of the one noisy
proprio stream without violating shared-noise identity.

S34: Provide a deterministic evaluation/verification configuration distinct from
training: fixed selected terrain family/level and forward command, curricula off,
startup dynamics randomization off, observation noise off, nominal spawn/joints/
zero initial velocity (no reset jitter). Preserve physics, action mapping, sensors,
reward definitions, contact/success conditions and termination semantics. Mirror
pairs share a source terrain geometry and reflected task regions; nominal dynamics
avoid confounding asymmetric random parameters in this baseline. Randomized
robustness evaluation is not implicitly added. This default targets repeatable
environment checks, not a claim of paper evaluation protocol equivalence or full
trained-policy performance coverage.

## S33/S34 resolutions — Approved

User “33. yes 34. yes” approved named current clean AMP data and deterministic
evaluation defaults. No terminal snapshots, training networks or dataset loader.
