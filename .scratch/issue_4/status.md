# Issue #4 — status and decision history

Current status: performance Verify completed and passed on commit cbd6423 following explicit user authorization. Fresh169 regression tests and180 differential cases passed; four-env step 13.3510ms (-61.11%), observations 8.2434ms (-71.38%). All approved A1–A7 criteria passed; native lifecycle evidence reused after exact source-hash checks. User requested publishing the verified work and closing T13–T16; Verify evidence is included in the delivery commit. See performance-verification.md.

Previous delivery status: Verify authorized; latest checks passed, unified user acceptance pending. Ground-aligned side slope implemented (ADR-008 follow-up, cache revision 3): 159 tests passed; native slope check, compileall and diff check passed. User moved camera to (.35,0,.05) and confirmed self-occlusion resolved; former visibility blocker closed on user evidence. See verification.md.
Approval: user requested “进入plan阶段”, then “继续”.
Explore/Research/Specify remain approved. T01–T12 cover accepted contracts.
User explicitly invoked Implement previously and now explicitly approved Verify entry. Earlier stage-gating statements below are historical.
Earlier entries below are historical snapshots.

The user explicitly invoked setup, confirmed default labels, and approved
all configuration drafts and creation of missing labels with “yes”.
Scope: skills configuration supporting https://github.com/MrCCaesar/r3la/issues/4.

Decisions: GitHub Issues; default five labels; single-context domain docs;
retain issue-local ADRs and existing stage approval rules.

Files: AGENTS.md and docs/agents/{issue-tracker,triage-labels,domain}.md.

The environment task remains at Explore. Its later stages require approval.
Next: verify configuration and GitHub labels.

## Verification completed

Setup complete. `git diff --check -- AGENTS.md docs/agents .scratch/issue_4`
passed. `gh label list --limit 100 --json name` confirmed all five labels.
Four labels were created; existing wontfix was reused.
No simulation tests were needed for this documentation configuration.
Next: resume issue #4 Explore when requested.

## Explore started

User invoked grill-with-docs and explicitly requested Explore.
Current stage: Explore, active; requirements.md is Draft.
Read issue #4 and skill instructions; gathering repository and official-source facts.
First discussion: physical target, delivery boundary, acceptance scope.
No approval to advance to Research or implement environment changes.

## Explore round 1 approved

User answered “1. yes 2. yes 3. yes”: Go2 target; environment/data delivery;
bounded correctness acceptance. Recorded as R6–R8 in requirements.md.
Current stage remains Explore. Round 2: terrain coverage, traversal success,
and success semantics shared by terrain/velocity curricula.
Static inspection completed; no simulations or tests run.

## Explore round 2 approved

Q4 terrain coverage approved. Q5 physical success intent approved with explicit
requirement to balance assessment validity and implementation complexity.
Q6 corrected by user: terrain curriculum uses success; velocity curriculum uses
velocity tracking performance. Recorded as R9–R11.
Next questions: success assessment unit, timeout outcome, allowable contacts.
Success detector algorithms and thresholds remain deferred; stage is Explore.

## Explore round 3 approved

User specified one obstacle per sub-terrain, success by passing that obstacle;
timeout is unsuccessful; base collision is the only illegal contact, while
other leg-link collisions use paper contact penalties and do not directly reset.
Recorded as R12–R14, superseding the multi-obstacle route proposal.
Next: meaning of one obstacle for continuous terrain, completion versus landing,
and commanded locomotion scope. Stage remains Explore; no runtime tests run.

## Explore round 4 approved

Q10 clarified obstacle as one IsaacLab 3.0 sub-terrain of a single terrain type;
Q11 retained landing requirement; Q12 confirmed forward-only command scope.
Recorded as R15–R17. Next: successful-episode lifecycle, obstacle bypass/out-of-bounds,
and tracking-performance intent during dynamic maneuvers. Explore remains active.

## Explore round 5 approved

Q13–Q15 approved: success ends/reset episode; obstacle bypass is unsuccessful;
velocity curriculum uses overall tracking performance with maneuver transients.
Recorded as R18–R20. Next: paper evidence for observation/randomization scope,
then remaining requirement-level gaps. Stage remains Explore.

## Explore round 6 approved

Q16 approved AMP environment-data support only. Q17 clarified shared noisy samples:
environment supplies each noisy quantity once, runner/model composes module inputs.
Recorded as R21–R22. Preserve existing environment-history requirement.
Next: Decoder target noise semantics and depth-input/target consistency.
Stage remains Explore; no code changes or runtime tests.

## Explore round 7 approved; stage review pending

Q18 approved shared noisy proprioceptive reconstruction targets. Q19 approved
shared depth input/target, with depth noise explicitly added as TODO-01 for later work.
Recorded as R23–R24 in requirements.md.

Current state: Explore review prepared; awaiting explicit approval to conclude
Explore and enter Research. Earlier next-round entries are historical.
No production code or simulation tests performed. Research questions and
unapproved technical decisions are listed in requirements.md's final review.

## Research started — approved

Approval reference: user “批准结束 Explore，进入 Research”.
Explore is approved as clarified by R6–R24. Current stage: Research, active.
Parallel source investigations: observation lifecycle; terrain/success/curricula;
paper/rewards/randomization. Findings will be synthesized in research.md.
No production implementation or simulation experiment is authorized by this stage transition.

## Research review prepared

Created research.md and three cited supporting notes: research_observations.md,
research_terrain.md, research_paper.md. Static source investigation completed at
IsaacLab commit 346c74fe722ad371a6c663e3b384b3d172966d11 (clean checkout).
Parent GitHub issue retrieval succeeded; worker network failures did not prevent
reading current issue requirements. Author project site/code could not be verified.

Findings: spawn-origin hazards; success/curriculum semantic gaps; shared-noise
feasibility with terminal-history hazards; paper/reward/Go2 mismatches; unresolved
AMP/randomization and backend verification. Recommendations are unapproved.

Validation: document presence checks and git diff --check passed. No simulation,
numerical experiment, training or production changes. Static findings do not
certify runtime behavior. Next: user review and explicit approval for Specify;
then resolve the proposed choices without treating stage approval as acceptance
of every recommendation. Depth-noise TODO-01 remains deferred.

## Research documents consolidated

User requested merging all research notes into research.md. The full contents of
the three earlier supporting notes now appear as sections in research.md, with
source citations preserved and navigation updated to internal section links.
The three standalone notes were removed after checking content preservation.
Earlier filenames above describe historical artifacts, not current destinations.
Current stage remains Research review; Specify has not been approved.
Validation: all three transformed source bodies preserved, one document title,
internal navigation targets checked, no links to removed notes remain.

## Specify started — approved

Created Draft design.md and interfaces.md, and Proposed ADR-001 (terrain/task
regions) and ADR-002 (initial physics/renderer support scope).
Next: user decisions S1/S2, then dependent geometric, physical and data contracts.
No ADR Accepted; no production changes, simulation or tests.

## Specify S1/S2 accepted

User approved S1 with official terrains conventions and src/r3la/labs/terrains
placement. User approved S2 and deferred OVPhysX (TODO-02) and isaacsim_physx
(TODO-03). ADR-001 and ADR-002 are Accepted with approval references.
Next: S3 per-family traversal/completion geometry and S4 finite landing detector
structure. Numeric thresholds and new public APIs remain unapproved.

## Specify S3/S4 accepted

User “3. yes 4. yes” accepted per-family routes and finite landing confirmation
structure. Recorded in design.md and accepted ADR-003; numeric landing criteria
remain open. Next proposed choices: S5 terrain success-rate statistics/initial
thresholds and S6 actual-attempt velocity tracking score. Stage remains Specify.

## Specify S5/S6 accepted with amendment

User accepted terrain success-rate window/thresholds but replaced maximum-level
hold with random return to lower levels. User accepted normalized actual-attempt
velocity tracking score. design.md records approval and supersession.
Next: S7 exact top-level recycling and S8 velocity aggregation/update behavior.
Numeric landing and Go2 difficulty/speed bounds remain undecided.

## Specify S7/S8 accepted

User “7. yes 8. yes” approved lower-level recycling and velocity-course update
rules including numeric starting defaults. design.md/interfaces.md updated.
Next: S9 canonical five-frame proprioception/reset padding; S10 terminal/reset
snapshot contract. No production implementation or runtime checks.

## Specify S9/S10 clarification under review

S9 data contents/history length/time order/commands/joint order approved; padding
must follow installed defaults. Static source confirms reset-zero then first-sample
backfill (returned history repeats first measurement). AMP terminal state and other
boundary metadata approved. Terminal proprio-history inclusion is not approved;
user requested research on excluding it. Targeted findings appended to research.md.

## S10 terminal WM scope resolved by user correction

User approved other terminal fields but questioned the added terminal WM sample
because reconstruction targets correspond to actual WM input instants. Rechecked
paper equations (7)–(9). Current design omits terminal noisy proprio history and
extra terminal noisy sample; preserves clean AMP/critic terminal data, boundary
masks, reset observations and sensor age. Timeout/latent compatibility remains
to specify separately. Superseded alternatives remain recorded in research/design.

## S10 final user amendment

User removed terminal clean AMP/critic states. No additional terminal snapshots
for proprioception, AMP or critic are required. Normal AMP support, normal
observations and boundary/sensor-age markers remain. design.md/interfaces.md
contain the authoritative amendment; older terminal-retention decisions are
superseded. Stage remains Specify; no code or simulations changed.
Next: remaining observation/physics/landing contracts and consumer timeout
semantics, without reintroducing terminal exports implicitly.

## Specify continuation: S11–S13 proposed

Rechecked official local observation callbacks and current project noise/cadence.
Proposed explicit frames/relative-value conventions, existing noise magnitudes,
and 200 Hz physics / 50 Hz control / 10 Hz depth cadence. Await user decisions.
No terminal snapshots reintroduced. No production code or runtime tests.

## Specify S12/S13 accepted with sensor amendment

User approved noise defaults and rates, reducing body and four foot target scans
to 10 Hz. Separate critic terrain scan remains 50 Hz. Updated design/interfaces;
S11 has no user answer and remains pending. Next: obtain S11 answer, then specify
low-rate target synchronization/reset validity and remaining sensor parameters.
No production code or runtime tests performed.

## Specify S11 accepted; S14–S16 proposed

User approved S11 observation semantics. Drafted sensor bundle synchronization,
metric depth layout/validity and scan geometry/frame/value conventions. These
choices await approval. No new terminal exports; TODO-01 remains deferred.
No simulation or tests run; only source inspection and document updates.

## Specify S15/S16 approved; S14 source investigation

User approved depth and scan contracts, requested inspection of default sensor
behavior before S14 decision. Native lazy scheduling and subclass reset invalidation
verified; moving-camera pose and partial-reset backend behavior require attention.
Findings appended to the single research.md; no standalone research files created.

## S14 default-behavior investigation complete (static)

Native schedule and reset invalidation are suitable foundations. Found camera pose
flag default false and Newton partial-reset full-buffer render risk. Revised S14
proposes native scheduling, explicit moving-camera pose refresh and row-isolated
held output snapshots; awaits approval. S16 foot-center/base-yaw needs an adapter,
not merely ray_alignment=yaw on a foot. No runtime experiment performed.

## Revised S14 accepted; S17/S18 proposed

User approved native scheduling plus camera-pose refresh/output isolation.
Accepted ADR-005 records alternatives and trade-offs. Drafted complete clean
critic feature order (273) and existing joint-position action mapping (0.5 scale).
Await S17/S18 decisions; physical thresholds/calibration remain pending.
No production changes or runtime tests.

## Specify S17/S18 accepted; S19/S20 proposed

User approved critic layout and action mapping. Next: consistent terrain-relative
height/Go2 target, and normal-force threshold/history semantics for contacts.
Reward formula differences are being reconciled against R3; no automatic parameter
or production changes. No simulation or tests performed.

## Specify S19/S20 accepted; S21/S22 proposed

User approved height/contact choices; ADR-006 Accepted. Next: speed range and
attempt duration, and Go2 terrain difficulty ranges. Geometry defaults are proposals,
not tested limits. Landing thresholds depend on these geometric choices.
No production changes or runtime tests.

## Specify S21/S22 accepted; S23/S24 proposed

User approved speed/time defaults and Go2 terrain ranges with ten levels.
Next: measurable finite-landing criterion and native stratified difficulty mapping.
These defaults have no runtime/learning validation. Stage remains Specify.

## Specify S23/S24 accepted

User narrowed landing roll/pitch bounds to strict absolute <30 degrees, accepted
other S23 criteria and S24 native difficulty sampling. ADR-003 updated with numeric
approval. Next: S25 stance reward convention and S26 invalid-height handling.
No production changes or runtime tests.

## Specify S25/S26 accepted; S27/S28 proposed

User approved stance formula/gates and all-invalid-height policy. Next: provisional
simulation camera calibration and terrain task dimensions. No real-camera calibration
or hardware geometry validation is claimed. No code or simulation changes.

## Specify S27/S28 accepted with platform amendment

Camera defaults approved. User changed box/stair top size to 1.2 m, recorded and
communicated as square 1.2x1.2 m top surfaces; other S28 values retained.
Next: completion-region margin S29 and tilted/mirrored terrain semantics S30.
No production changes or runtime tests.

## Specify S29/S30 accepted with amendments

Platforms now 1.5x1.5 m; margin 0.15 m; completion regions 1.2x1.2 m.
Tilted/mirrored variants limited by user to slopes and stairs; requirements and
ADR-001 updated to supersede broader scope. Next: S31 randomization and S32 reset/
training disturbance defaults. No production changes or runtime tests.

## Specify S31/S32 accepted with disturbance removal

User accepted startup randomization and removed push_robot from S32. Remaining
reset settings retained. No periodic pushes or replacement forces/impulses.
Next: S33 named clean AMP support fields and S34 deterministic evaluation defaults,
then integrate current authoritative contracts and audit unresolved details.
No production changes or runtime tests.

## Specify S33/S34 accepted and documents consolidated

User “33. yes 34. yes” approved named current clean AMP data and deterministic
evaluation. Consolidated all current accepted choices into design.md/interfaces.md;
prior discussion preserved in history/design-discussion.md and
history/interfaces-discussion.md. No additional research files created.

Current approval frontier: S35/P1 native extension seams (Proposed ADR-007), then
P2 remaining physical geometry and P3 reward/termination edge contracts. No Plan
approval requested yet because these contracts are incomplete.
Static hook/source review supports the proposed seams; no runtime compatibility
claim. No production changes or tests/simulations performed.

## Revised S35 after native-lifecycle reconsideration

Still Proposed. Reuse native pre-reset curriculum invocation, manager reset and
command countdown. Remove finalized-record/consumed-flag machinery. Stateful native
termination term owns task progress and pre-reset score; stateful native curriculum
term owns persistent statistics. Minimal CommandTerm adds per-family sampling only;
fixed commands use a native period exceeding episode length. Terrain/sensor seams
unchanged. design.md, interfaces.md and ADR-007 synchronized. No production changes
or runtime tests; source review and document whitespace checks only.

## Revised S35 approved; next geometry questions S36/S37

User “yes” approved the revised S35. ADR-007 Accepted; design/interfaces synchronized.
Specify remains active; no Plan or implementation approval. Proposed next decisions:
S36 stair width 1.5 m aligned to top platform; S37 finite gap depth 1.0 m with floor
excluded from valid completion support. These numeric proposals are not approved.
Only documentation changed; git diff --check performed, no simulation/runtime tests.

## S36 amended / S37 approved

User requires optional stair/platform width matching, referencing native holes;
fixed-width-only S36 is superseded. S37 finite 1.0 m gap depth accepted. Source
inspection confirms holes changes four-sided stair topology and omits border meshes.
Open S38: adapt width behavior to +X single flight vs reproduce four-sided geometry;
S39: proposed default holes=False, fixed per config. No implementation or simulation.

## S38/S39 approved

User “38. yes 39. yes” accepts +X single flight with native-inspired holes width
behavior, default False, configurable True. Four-sided native pyramid topology is
not adopted. S40 lateral envelope and S41 tilt/difficulty coupling proposed next.
Specify remains active. Documentation only; no runtime tests or simulation.

## S40/S41 approved; S42/S43 pending

User “40. yes 41. yes” approved stair width envelope and shared difficulty for
height/tilt. Updated design/interfaces. Next proposals: slope transitions inside
2 m section; rough-grid representation for rock patch. These remain unapproved.
Specify active; no Plan/implementation approval. Documentation checks only, no
simulation or runtime tests.

## S42/S43 approved; native random-grid compatibility inspected

User approved slope transitions and rough-grid geometry, requested source lookup.
Native random_grid_terrain cannot directly satisfy approved positive-only heights,
exact divisibility without border, no central platform, and localized patch.
Research/design/interfaces updated; S44 local adaptation proposed, not approved.
No production code or runtime tests. Static source inspection and git diff --check.

## S44 approved; S45/S46 proposed

User “44. yes” accepted local random-grid adaptation. Updated design, interfaces
and accepted ADR-001 refinement. Proposed next: training initialization at level 0
and six equal-proportion terrain families with ordinary/tilted stairs separated.
Specify remains active; these proposals do not authorize Plan or implementation.
Documentation-only validation: git diff --check; no simulation/runtime tests.

## S45/S46 approved with amendments

User chooses native max_init_terrain_level=5, verified to include initial levels
0..5, and ordered family proportions .2,.2,.1,.2,.2,.1. Previous zero-level/equal-
weight proposals superseded. S47 proposes ten columns (2,2,1,2,2,1 by family).
Specify remains active; no implementation. Static source/document checks only.

## S47 approved with amendment

User “47. 10行 20列” sets num_rows=10 and num_cols=20, superseding the proposed
ten-column default. Family column counts: box 4, gap 4, ordinary stairs 2,
tilted stairs 4, side slope 4, rough grid 2. Updated design/interfaces.
Remaining Specify contracts: placement/gates, support membership, ray bounds,
slope mesh tolerance and reward/compatibility edge conventions. No stage advance.
Documentation-only change; git diff --check, no runtime tests or simulation.

## Specify continuation — S48/S49 pending

User requests remaining design clarification. Reviewed unresolved contracts and
removed stale initial-level/family items from P2. Proposed common obstacle placement
and nominal spawn (S48), plus explicit slope/grid/gap exit landing rectangles (S49).
These are not approved. Gates, support-surface membership, ray bounds, slope mesh
tolerance and reward edge conventions remain to resolve. Documentation-only work;
no simulation or production edits.

## S48/S49 approved; S50/S51 pending

User “48. yes 49. yes” accepts common tile layout/spawn and explicit exit landing
rectangles. Updated design/interfaces. Next proposals: ordered segment-crossing
gates with rollback on retreat, and sampled base-center corridor bypass behavior.
These remain Proposed; no implementation or stage advance. Documentation checks
only, no runtime tests/simulation.

## S50/S51 approved; S52 support attribution proposed

User “yes” approves both gate crossing and corridor bypass proposals. Updated
contracts. Source inspection identifies native terrain-filtered aggregate contact
points; S52 proposes geometric target-surface membership with 0.03 m plane tolerance.
Not yet approved or runtime validated. Specify active; no production changes.

## S52 approved; S53/S54 proposed

User “yes” approves contact-position support attribution and 0.03 m tolerance.
Updated design/interfaces and ADR-003. Proposed finite scan rays (+2 m launch,
5 m reach) and side-slope mesh spacing/error limits (0.05 m / 0.001 m). Still
Specify; no implementation, simulation or numerical geometry verification.

## S53/S54 approved; S55/S56 pending

User “yes” approves finite terrain-ray bounds and slope mesh accuracy. Updated
contracts. Source inspection confirms RewardManager dt multiplication and current
project smoothness suppression for first two actions. Next proposals S55 native
reward time scaling, S56 action-rate/smoothness reset conventions. Still Specify;
no production implementation or runtime tests.

## S55/S56 approved with startup amendment

User accepts native dt scaling and changes second-order smoothing to active from
first action with zero pre-episode history: ||a0||², ||a1-2a0||², then standard
second difference. Supersedes proposed first-two-step suppression. Design/interfaces
synchronized; implementation must later remove that suppression. Specify active.
No code edits or runtime tests; document whitespace check only.

## Specify continuation — S57/S58 proposed

User requests continuation. Remaining proposals now recorded: contact-event airtime
formula with existing 0.5 s threshold/+0.5 weight but no command gate (S57), and
native termination/truncation flags including coincidence behavior (S58). Neither
approved yet. Need final contract consolidation and acceptance coverage audit before
requesting Plan. No production changes or runtime tests.

## S57/S58 approved; Specify audit found staircase ambiguity

User “同意” accepts S57/S58. Updated authoritative conventions. Audit found four
risers versus four separate tread runs leaves platform X ambiguous; S59 proposes
three intermediate treads and fourth level as platform, with explicit coordinates.
Do not mark Specify complete yet. Still need explicit tilted-stair transform,
final TerrainLayout/data-key contracts and consolidated reward/acceptance table.
No production changes or runtime tests. git diff --check performed.

## S59 user amendment accepted; S60/S61 pending

Fixed stair count and platform-as-highest-tread interpretation superseded. Count
must derive from region dimensions/tread depth; platform excludes highest tread.
Updated design/interfaces/ADR-001. Proposed S60 longitudinal budget and integer
count/remainder policy; S61 separate but equal-height platform. These are unapproved.
Check resulting total heights against ray coverage when geometry is resolved.
Specify active; no production edits or runtime tests.

## S60/S61 user corrections; S62 reconciliation required

User requests native staircase count and rejects equal-height platform. Withdraw
proposed 3.9 m budget and one-sided floor formula. Source review reveals native
actual platform dimensions are residual, potentially conflicting with exact1.5 m
platform and S40 width envelope. S62 asks explicit priority before setting geometry;
no implicit approval of footprint/border or altered platform dimensions. Specify
remains active; no production changes or simulation.

## S62 approved and immediate completion correction applied

User selects native residual stair platform; then corrects center-based completion
to actual-boundary inset. Latest instruction is authoritative: parameter1.5 m,
actual remaining platform, inset0.15 m each edge. Preserve box dimensions; supersede
fixed stair1.5/1.2 m and conflicting S40 width formula. Updated design/interfaces/
ADR-001. Stair region/border and tilt transform remain open. Specify active;
no implementation or runtime tests. git diff --check only.

## Specify continuation — S63 proposed

Next unresolved item: native stair formula inputs. Propose full10x10 m count region,
border0, native formula giving15 treads, residual1m platform, additional platform
rise and max centerline height3.68m at d1. Single +X flight remains placed at x3;
platform x7.5..8.5. These numeric defaults are not yet approved. Explicitly surface
height change before freezing tilted geometry or scan-coverage verification.
No production changes, simulation or runtime tests. Documentation check only.

## S63 amended; S64 remaining-region interpretation pending

User rejects full-tile count inputs; requires entrance-excluded remaining space.
Withdraw proposed N15/full-tile geometry. Existing x3 entrance implies candidate
x3..10 (7m), not8m obtained by subtracting approach length alone. S64 presents7x10,
border0 consequences including nonsquare1x4 platform and unchanged2m corridor.
These input details remain unconfirmed. Specify active; documents only.

## S64 approved

User “yes” approves7x10 m remaining region,border0 and derived10 treads/1x4 m
platform. Completion actual inset0.7x3.7 remains subject to2 m corridor. Updated
design/interfaces/ADR-001. Untilting default platform x6..7,y3..7,height11h;
tilt transform still unresolved. Next: tilted-stair surface/pivot and final
interface/reward/acceptance consolidation. Specify active, no stage advance.
Documentation-only check: git diff --check; no runtime tests or simulation.

## Specify continuation — S65 proposed tilted stair construction

User requests continuation. Propose lateral height shear about y5 with unchanged
XY dimensions and centerline heights, plus final0.5 m approach transition to the
same tilted ground reference. This avoids hidden low-side steps but changes the
last part of the approach, so explicitly pending approval. No code/simulation.
After resolution: geometry/schema and full reward/acceptance consolidation.

## S65 approved with horizontal entrance/platform amendment

User retains tread shear, requires horizontal entrance/platform. Removed proposed
approach transition and platform tilt. Updated design/interfaces/ADR-001. Record
variable first/final boundary heights and need to validate low-side joins without
masking prescribed surfaces with underlying flat ground. Remaining work: consolidate
final schema/keys, reward table, acceptance coverage and consistency audit before
Specify closure request. No production code, simulation or runtime tests.

## Specify final contract consolidation — S66/S67 proposed

User requests continuation. Prepared reviewable final metadata names, TerrainLayout
records and per-family gates in interfaces.md (S66), consolidated16-term reward
table and acceptance coverage in design.md (S67). Both remain Proposed. They do
not authorize stage advancement. After approval: final consistency consolidation,
then explicit Specify closure/Plan request. No production edits/tests/simulation.

## S66/S67 approved; consolidated Specify ready for closure review

Archived full pre-consolidation design/interfaces to history/*-through-s67.md.
Current design/interfaces retain approved behavior only, replacing obsolete geometry
and pending labels with native count/residual platform, horizontal entrance/platform,
accepted schema/keys, complete reward table and acceptance coverage. Stage advancement
still requires explicit approval. git diff --check and document consistency scans;
no runtime tests. Next authorized action after approval: prepare plan.md, not code.

## Specify closed by explicit user instruction

User “结束 Specify” approves closure only. Do not infer Plan entry from this reply.
Current design/interfaces are approved; history and ADRs retained. Await explicit
Plan authorization before creating plan.md. Documentation whitespace check only.

## Plan started — explicitly authorized

Created Proposed plan.md: twelve verifiable slices, dependencies and acceptance
traceability. Read GitHub #4 and issue requirements/research/design/interfaces/ADRs.
Backend scope follows ADR-002; flagged conflicting acceptance-table wording.
Next: user breakdown review and explicit publication authorization.
No production edits, simulations or GitHub writes.

## Plan publication completed

User “yes” approved breakdown and publication. Created #5–#16 under #4 with
ready-for-agent and native blocking relationships; GraphQL readback verified all
bodies, titles, labels, parents and dependencies. Mapping is in plan.md.
No production implementation or simulation. Next: explicit Implement approval,
then T01 / #5. Parent issue body/state unchanged.

## Implement started — explicit user authorization

User invoked mattpocock-skills:implement and requested Implement entry. Starting
T01 / #5, preserving pre-existing working changes. Uses repository .venv/bin/python.
TDD seams: approved layout/mesh/generator/reset contracts. Two-axis review started.
No commit/push or GitHub edits authorized by this implementation request.

## T01 implementation progress

Box layout/mesh/generator/importer and task reset wiring implemented. Latest full
project pytest: 7 passed; bounded two-environment Newton five-step run prints
All checks passed. T01 remains in progress: full spawn footprint validation,
complete runtime region conversion and simulator partial-reset assertions remain.
See implementation.md for exact commands, outcomes and two-axis review findings.
Continue approved Implement from T01; do not ask for stage-entry approval again.
No commits/pushes, issue changes or final Verify stage entry.

## T01/T02 continuation completed

User “继续实施” reaffirmed Implement authorization. T01 remaining footprint,
runtime metadata and real partial-reset checks resolved. T02 native attempt term
and terrain contact filter implemented. Latest suite 26 passed; two-env bounded
normal/failed landing run exited0 with actual pre-reset success capture.
Independent Standards/Spec review findings addressed. Exact commands/limitations
in implementation.md; logs t01-partial-reset.log and t02-landing.log.
T03–T12 remain; next frontier T03/T04/T06/T07/T08/T09/T11 per approved plan.
No GitHub issue closures/edits, commits or pushes. Final Verify not entered.

## T03 continuation completed

Implemented #7 gap mesh/layout/config and two-gate traversal integration. CPU suite
36 passed; bounded two-env far landing and actual floor/horizontal wall collision
checks exited0. Independent reviews' degenerate sidewall finding fixed/tested.
Combined synthetic/native evidence and limitations recorded in implementation.md.
Registered task currently has box+gap; six-family integration and observations
remain incomplete. Next ordered slice: T04 / #8 ordinary staircase.
Implement authorization persists. No final Verify, issue writes or commits.

## T04 continuation completed

Implemented #8 ordinary stairs: native count/residual platform, both holes modes,
actual-boundary inset, single+X flight, metadata/cache/runtime tensor integration.
Suite57 passed; two-env native holesFalse/d1 and holesTrue/d0 landing checks
exited0. Resource-bound/error-contract findings from review fixed and tested;
Spec follow-up found no remaining concrete defect. Parameters, safety guard,
commands and evidence limits recorded in implementation.md.
Registered families now box/gap/stairs. Next ordered slice: T05 / #9 tilted stairs
and matched mirror. Implement authorization persists; final Verify not entered.
No issue writes, closures, commits or pushes.

## T05 continuation completed

Implemented #9 tilted treads and matched reflection. Horizontal entrance/platform
retained; partitioned ground leaves negative low-side surfaces exposed. Both signs,
holes modes, endpoints, signed joins, asymmetric regions and cache identity tested.
Suite74 passed. Three native configurations exited0 in serial two-env runs (canonical, mirror,
holesTrue; canonical repeated at final1e-5 tolerance), covering actual platform outcomes and analytic collider height probes.
Two-axis review found no concrete new defects. Details/commands/limits in
implementation.md. Registered families now box/gap/stairs/tilted_stairs.
Next ordered slice: T06 / #10 side slope and mirror. Implement authorization
persists; no final Verify, GitHub writes, commits or pushes.

## T06 continuation completed

Implemented #10 side slope and exact matched mirror, explicit .5m transition
segments, <=.05m grid and complete triangle-interior error bound below1mm.
Five implemented families registered; no added learner features or tilt layers.
Suite87 passed; canonical/mirror two-env native landing and height probes exited0,
maximum measured error about.456mm. Two-axis review found no concrete defects.
Commands, mathematical bound and evidence limits in implementation.md.
Next ordered slice: T07 / #11 random rock grid. Implement authorization persists;
no final Verify, GitHub writes, commits or pushes.

## T07 continuation completed

Implemented #11 deterministic positive rough grid:100 exact cells, no central
platform/gaps, shared generation sample, native cache parity and runtime metadata.
All six terrain families now register with approved weights; CPU generator confirms
4/4/2/4/4/2 columns. Suite95 passed; serial d0/d1 two-env native landing/cell-top
checks exited0, heights unchanged after reset. Two-axis review found no concrete
defect; stale aggregate comment corrected. Commands/limits in implementation.md.
Next ordered slice: T08 / #12 shared proprioceptive history and canonical actions.
Data/sensor/reward/curriculum/evaluation integration still incomplete. Implement
authorization persists; no final Verify, issue writes, commits or pushes.

## T08 continuation completed

Implemented #12 shared proprio210/five-frame native history, canonical selectors,
official actionmapping and explicit checked-input utility. Initial commands fixed
for default attempt duration; per-family custom sampler remains T11.
Suite109 passed; two-env4-step native history/action/partial-reset/timeout check
exited0. Two-axis review found no concrete defect. Action checker is explicit, not
auto env.step enforcement; native manual-reset append behavior documented in
interfaces.md. Exact commands, lint limits and scope in implementation.md.
Next ordered slice: T09 / #13 depth and height-scanner contracts. Implement
authorization persists; final Verify, issue writes and commits remain unperformed.

## Continuous implementation authorization and T09–T11

User requested completion of every ticket before returning for review. Continue T12
without asking after individual tickets. Final Verify stage approval stays separate.
T09 calibrated depth/scan adapters and metadata implemented; native two-env sensor
checks passed, including an independent known-plane fixture. Approved production
camera x=.30 m self-occludes all tested nominal-pose pixels (<.1 m near clip):
outputs correctly zero+invalid. This material visibility limitation is retained for
user review; no unapproved pose/renderer visibility change was made.
T10 sixteen reward numeric fixtures, startup applied parameters, clean privilege273
and named AMP implemented. T11 separate persistent terrain/speed statistics and
native fixed-attempt commands implemented. Combined native two-env51-step check
exited0: applied parameter readback, terminal-step duration, pre-reset migration,
next-command bounds and all-invalid height behavior passed.
User feedback fixed terrain trimesh package to lazy_export()+__init__.pyi; six
exports resolve without eager mesh/config imports. Two-axis review found missing
mask shape/dtype validation (fixed with rejection tests), stale leg-contact naming
and unused scanner parameter (fixed). T12 serial evaluation remains in progress.

## T12 completed — unified review handoff

All approved tickets T01–T12 have code, tests and synchronized documentation.
Complete suite141 passed; compileall and scoped Ruff passed. Seventeen final native
cases exited0: T09 sensor, combinedT10/T11 dynamics, nine deterministic evaluation
cases, six current full-stack contact/geometry cases. Each used2 envs, no visualizer,
serial bounded execution with preflight resource checks. Both mirror pairs share
canonical geometry; d1 stairs platform2.53 m lies within approved ray reach.
Native RSL-RL wrapper forwards nested observations/done/timeouts; learner scope and
missing runner assembler remain documented. Two-axis review findings fixed and
rechecked with no remaining concrete findings.

Terrain lazy feedback fully addressed at both layers: lazy_export()+stub package
and native configclass callable ResolvableString function references defer mesh
imports until actual generation. Final141-test suite reran after this change.

Review documents: docs/parkour.md, implementation.md, verification.md (Draft),
t12-eval-results.json, t12-contact-results.json and t12-canonical-pairs.json.
Production approved camera mount self-occludes all tested nominal-pose depth pixels;
correct invalid encoding is implemented, useful terrain visibility remains an
explicit user design-review item. No unapproved pose/renderer changes.

Next: user unified review and camera decision; final Verify requires explicit entry
approval. No commits/pushes, GitHub edits/closures, training or final Verify performed.


## Cleanup and commit authorization — 2026-11-06

User requested cleanup of unrelated intermediate files and commit of current
changes. Removed completed ticket-publication request bodies/helper scripts and
local Python/test caches. Retained requirements, design/history, ADRs, published
ticket mappings, test scripts and verification logs as traceable evidence. Earlier
references to publication helpers describe historical work; those helpers are no
longer needed after publication. No GitHub edits or push authorized/performed.


## Remote delivery authorization

User requested pushing to remote and closing the corresponding sub-issues while
keeping Issue#4 open. Scope: performance T13–T16, GitHub#17–#20. Push current swap
branch with final Verify evidence, then close these four completed tasks. Parent
Issue#4 and earlier task issues are not included in this closure operation.


## Native camera investigation follow-up

After delivery (swap85a7bb0 pushed; user-authorized sub-issues#5–#20 closed and
parent#4 kept open), user requested native Camera partial-reset testing. Completed
a two-env native-class experiment: another row's capture overwrites row1 depth
without updating row1 capture metadata. Controlled scene motion changes40645 of
76800 pixels; ordinary static-image comparisons remain unchanged. Details and
limitations: native-camera-isolation.md. No production changes or new commit.


Metadata training discussion opened under user-invoked grill-with-docs. Facts and
open consumer decisions in metadata-training-discussion.md; no schema/code change
approved or performed.

User requested installed RSL-RL PPO/runner data investigation. Completed source
inspection of 5.5.1 and a CPU TensorDict storage experiment; findings captured in
rsl-rl-training-data.md. No simulation, training, production edit or stage advance.
Metadata removal and training interface changes remain unapproved.

## Metadata removal follow-up implemented

User explicitly requested removal of unnecessary metadata exports and consistency
checks, superseding the preceding unapproved proposal. Removed metadata group,
metadata/bundle exports and six-sensor observation validation; target terms now
read only their selected sensor. Native scheduling, held buffers and internal
validity remain. ADR-010 and interface/design amendments record the new contract.
164 pytest tests passed; native smoke scripts updated but not run. See
metadata-removal-verification.md. No commit/push. Runtime Verify remains a next
step; no new performance result claimed.

## Metadata removal — Formal Verify passed

User approved Verify. Fresh 164-test regression, compileall, whitespace and removed
lazy-export/config probes passed. Three serial 2-env headless GPU checks exited 0:
sensor sampling/calibration/partial-reset isolation; evaluation/RSL-RL wrapper
observations and timeout auto-reset; dynamics/AMP/termination/all-invalid height
reward (51 steps). Details and exact commands: metadata-removal-verification.md;
logs metadata-verify-*.log. No production edits during Verify. No training or new
speedup claim; runner input compatibility remains a separate known limitation.
No commit/push or issue edit. Verification complete; ready for user review.

## Final delivery authorization

User explicitly requested cleanup, commit, push and closure of parent Issue #4,
superseding the earlier instruction to keep it open. Removed the completed native
camera one-off probe and verbose log; retained its structured evidence/report and
all metadata removal verification logs. No production change since passed Verify.
Delivery will publish the current swap branch and close #4 after successful push.
