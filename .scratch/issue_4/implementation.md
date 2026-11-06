# Issue #4 Implementation — Ready for user review

Current handoff (2026-11-05): T01–T12 code and implementation checks complete;
awaiting user review and separate final Verify stage approval. The production
camera visibility limitation below remains an explicit review item.

Authorization: user invoked implement and requested entering Implement. Plan remains approved; no further stage-entry confirmation needed to continue approved implementation. Final Verify remains separately gated. No commit/push or issue edits performed.

## T01 / #5 — Implemented; implementation checks passed

Implemented deterministic immutable box layout records and mesh/config pair; native generator subclasses capture sampled difficulty through cache hits/misses and attach correctly placed records. Native importer exposes table and device spawn positions. Registered task currently selects an explicitly named box-only configuration pending the remaining family slices. Reset event writes entrance pose, zero velocities and nominal-scaled joints for selected environments, including native slice IDs. Removed push event in line with approved scope. Existing user terrain aggregate retained.

Tests exercise box endpoints, target regions, watertight mesh, invalid difficulty, cache hit/miss mesh agreement, global placement, assigned partial reset, and registered config loading. Corrected prior registration test which asserted absence of the task. Tests mock the external simulator write boundary, not project geometry logic.

## Executed checks

- `.venv/bin/python -m pytest tests/test_parkour_terrain.py -q`: initial RED (layout module absent); successive implementation cycles passed.
- Ordinary pytest startup initially failed on unrelated globally discovered ROS plugin missing lark. Set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` for project tests.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: latest 7 passed, 35 upstream TorchScript deprecation warnings.
- Targeted `.venv/bin/ruff check` over new terrain modules and tests: passed after fixes.
- `.venv/bin/python -m compileall -q src/r3la/labs/terrains src/r3la/tasks/velocity tests`: passed. No static type checker available in .venv; compileall is syntax checking, not type checking.
- Resource probe: RAM available about 19 GiB; external GPU probe 7793/8188 MiB free. Sandbox did not expose CUDA; simulator run outside sandbox.
- Native zero-agent CLI alone did not discover project registry; explicit `import r3la.tasks` resolves it.
- First Newton run exposed slice env IDs in native reset; fixed and added regression coverage.
- Latest bounded command (stdout/stderr in t01-smoke.log):

```bash
timeout 150s .venv/bin/python -c 'import warp as wp; wp.config.enable_backward=False; import r3la.tasks; from isaaclab_rl.entrypoints import run_zero_agent_cli; raise SystemExit(run_zero_agent_cli())' --task R3la-SWAP-Parkour-UnitreeGo2 --num_envs 2 --max_steps 5 --device cuda:0 --viz none env.scene.terrain.terrain_generator.num_rows=2 env.scene.terrain.terrain_generator.num_cols=1
```

Run exited with code 0, reached scene/reset/step and printed `All checks passed!`. This proves bounded loadability, not successful obstacle climbing or final sensor/observation contracts. Current legacy observation dimensions remain proprio168/privilege269, to be corrected in T08/T10.

## Two-axis code review

Used implement, tdd and code-review skills. Standards and Spec reviewers independently examined current T01 changes (working-tree changes; pre-existing user edits excluded conceptually rather than treating HEAD as a clean task baseline).

Fixed duplicated mesh XY constants by deriving from layout; removed new mutable call default flagged by Ruff; strengthened cache comparison to vertices/faces and uncached output; added finite metadata/normal/completion checks. No claim that all review findings are resolved.

Earlier T01 review checklist (resolved by continuation below):

- Full safe robot footprint feasibility against approach, including reset jitter.
- Complete setup-time metadata validation and once-only device conversion for gates, regions, support planes, difficulty and IDs before T02 uses them; current importer copies spawn positions only.
- Explicit simulator partial-reset assertion beyond mocked write checks.
- Improve record construction readability (keyword arguments rather than long positional tuple).

T12 owns nominal evaluation reset and six-family aggregate wiring. The following continuation supersedes this earlier progress snapshot.


## Continuation — T01 completed, T02 implemented

T01 now validates immutable layout/placement data, box geometry/support agreement,
all relevant numeric shapes and finite values, nonempty completion/corridor and
ordered gates. Importer converts transform/spawn/yaw, bounds, gates/counts/masks,
local/world support planes, actual difficulty and IDs once onto the device.
Canonical strings retain an indexed generation-time table. Reset uses actual
layout yaw. Conservative whole-robot collision radius is computed once from the
loaded Newton articulation's joint-anchor path lengths and collision sphere
radii/margins: 0.756211 m for the loaded Go2. This envelope permits any joint
rotation, so covers the specified reset perturbations and yaw. Adding 0.2 m jitter
fits the 1 m approach half-width. Rejected geometry is not clipped or altered.

T02 adds a single native ParkourAttemptState termination term with ordered segment
crossings/rollback, sampled corridor bypass, rolling ten-sample support, strict
attitude and vertical speed criteria, terrain-filtered contact point attribution,
failure precedence and pre-reset tracking integral/duration. Uses common_step_counter
for exactly-once transition updates; selected reset clears only selected state.
Existing native base-contact and timeout terms remain separate. Contact history is
four physics samples; static terrain is filtered by its actual shape path, not a
nonexistent rigid body. No terminal observations added.

Native quaternion API source was verified to use xyzw. Internal root state/math
uses that native order. Approved project AMP wxyz export remains a T10 obligation,
not a change to that contract.

### Checks executed in this continuation

- RED layout metadata regression reproduced malformed/inconsistent geometry acceptance;
  fixed and passed. RED attempt tests initially failed because term did not exist.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: **26 passed**, 35
  existing upstream TorchScript deprecation warnings.
- Targeted Ruff over new terrain modules, attempts/reset event, tests: fixed one
  long line; final lint result recorded below.
- `.venv/bin/python -m compileall -q src tests`: passed. No pyright executable or
  .venv type checker available; static type checking remains unrun.
- RAM available about 18 GiB; GPU 7793/8188 MiB free before each bounded run.
- `timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none`:
  exit 0; T01 PASS, complete runtime tensors + untouched-row pose/joint assertions
  on partial reset + five physics control steps. Log: t01-partial-reset.log.
- Same command with `--landing`: exit 0; T02 PASS for finite real terrain-filtered
  contact points, actual normal landing success and failed side/base landing.
  At most two environments, fifty landing-control steps and no visualizer. Log:
  t02-landing.log. A test-only native pre-reset curriculum observer copies success
  before clearing; bypass cannot satisfy the success assertion.

Early smoke entry attempts failed on unresolved preset/launcher arguments; fixed
by native resolve_task_config after consuming launcher args. First contact filter
attempt failed because static terrain has no rigid body; native shape filtering
resolved this without changing task physics. First sideways landing fixture did
not contact the base; now deliberately places the sideways base in contact with
the platform. Normal landing is independently checked without penetration.

Synthetic tests cover supported-sample occupancy, distinct-foot count, final support,
expired/no-hit/wrong-surface support, attitude/speed limits, multigate high-speed
crossing/rollback, failure precedence, repeated reads, terminal tracking step and
partial-reset state isolation. These tests do not claim policy climbing capability.

Independent Standards review's malformed metadata finding fixed and regression
re-run by reviewer. Spec review's union-of-success/bypass smoke assertion finding
fixed with pre-reset success capture and the backend run repeated successfully.
No confirmed production defect remains from these reviews. Final Verify is still
separate; sensor adapter/reward/observation/curriculum and six-family integration
acceptance remains for T03–T12. Current observation dimensions are still legacy.
No commits, pushes or GitHub edits performed.


## T03 / #7 — Implemented; implementation checks passed

User “继续实施” continued approved Implement. Read GitHub #7 title/body/comments
(no comments); reused current accepted gap geometry and task predicates.

- Added immutable GapGeometry and gap layout: width0.2+0.6*d, depth1m,
  ditch x[3,3+width]/y[4,6], far landing length2m, target inset0.15m,
  two ordered gates. Invalid/degenerate dimensions and inconsistent support
  metadata fail setup. Boxes and gaps remain untilted.
- Five closed solids provide approach/far ground, two lateral walls and the floor.
  No continuous ground slab covers the ditch. Mesh/origin signature remains native.
- Registered task now uses PARKOUR_IMPLEMENTED_TERRAINS_CFG (box/gap, approved
  relative weights .2/.2). The older aggregate and box-only config remain available;
  complete six-family proportions remain a T12 integration obligation.
- Existing ParkourAttemptState handles gap crossing, retreat/rollback, bypass and
  target-only support without new termination rules. No changes to physical
  contact thresholds, action or observation contracts.

Affected files: layouts.py, trimesh mesh/config pair, aggregate/export wiring,
registered task configuration, gap/attempt/registration tests and native smoke.

### T03 executed checks

- RED tests failed while gap config was missing, then passed after implementation.
- Tests cover d=0/1, downward floor rays, horizontal wall rays, far support/regions,
  origin separation, cache consistency and mixed box/gap placement. Synthetic
  attempts place base beyond both gates inside completion while supplying floor,
  wall or valid far-landing support, isolating support attribution; also test rollback
  and bypass.
- Independent Standards and Spec reviews found a zero-width sidewall when tile
  height equaled6m. Added failing regression, rejected size_y<=6, then passed.
  Valid narrow tile5.8x6.1m retains positive-volume, watertight solids/nonzero faces.
  Reviewers independently confirmed the fix; no remaining production finding.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: **36 passed**,
  35 existing upstream TorchScript deprecation warnings.
- Scoped `.venv/bin/ruff check` on changed new modules/tests: passed.
- `.venv/bin/python -m compileall -q src tests`: passed. Static type checker still
  unavailable; syntax checking is not static type checking.
- RAM available around18GiB; GPU7793/8188MiB free checked before each serial run.

```bash
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family gap --landing
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family gap --landing --gap-contacts
```

Both latest runs exited0. Logs: t03-gap-landing.log and t03-gap-contacts.log.
Two environments only; at most5 entrance+50 landing+30 negative-contact control
steps in the second run; no visualizer. Normal far landing records actual success
at native pre-reset hook; failed side/base landing, partial reset, actual floor
support nearz=-1 and filtered horizontal terrain collision history also checked.
The explicit contact run uses d=1 so the full robot can fit inside the widest ditch.

Early negative-contact checks found no latest wall contact point. Newton can separate
an impact before the final substep; now test reads both live/pre-reset contact points
and terrain-filtered four-substep normal force history. Thresholds/physics unchanged.

Evidence limits confirmed by Spec review: native negative fixtures keep base before
far gate/outside completion, so lack of success there alone cannot prove geometric
support attribution. The independent synthetic tests isolate that predicate inside
completion. Horizontal force evidence proves terrain wall collision in the controlled
fixture, not a mesh-face identity. Analytic mesh rays separately verify the specified
far/lateral walls. Tests do not establish a policy's ability to leap the gap.

T03 implementation is complete; T04–T12 remain. No final Verify stage entry,
GitHub issue edits/closures, commits or pushes.


## T04 / #8 — Implemented; implementation checks passed

User “继续实施” continued approved Implement. Read GitHub #8 title/body/comments
(no comments) and reconciled count/holes construction against installed native
pyramid_stairs_terrain source. Accepted S59–S66 govern the project single flight;
no native four-sided flight or forced square platform was introduced.

### Implemented behavior and affected code

- layouts.py: immutable StairGeometry records with actual count/rise/tread depth,
  holes mode, per-tread bounds/planes and residual platform bounds/height. Factory
  derives geometry, ordered entrance/platform gates and actual0.15m platform inset
  together. Invalid dimensions, empty insets, discontinuous tread metadata and
  inconsistent horizontal planes/support surfaces fail with contextual ValueError.
- trimesh mesh/config pair: one ascending +X flight; lower treads shrink laterally
  with holes=False, fixed configured span with holes=True. Missing side steps do
  not add infinite pits or reset conditions. Closed positive-volume solids share
  layout dimensions; `(meshes, origin)` remains native. Platform is one rise above
  highest ordinary tread.
- terrain_importer.py: once-only padded device tread bounds/planes/count/valid mask,
  including empty masks for non-stair families. No new learner observations.
- Registered implemented-family aggregate now includes box/gap/stairs with relative
  weights.2/.2/.1. Final six-family column counts remain a T12 obligation.
- Tests cover endpoints/holes, analytic collision rays, changed parameters, cache
  identity/placement, highest-tread versus platform support and legal corridor.
  Native smoke supports --family stairs, --holes and endpoint --difficulty.

### Stair configuration semantics

ParkourStairsTerrainCfg uses step_width0.30m, step_height_range(.05,.23)m,
platform_width1.5m (count parameter), border_width0m and holes=False by default.
Count uses remaining tile space after x3 entrance, not full tile:
N=int(min((Sx-2b-p)//(2t)+1,(Sy-2b-p)//(2t)+1)); actual platform dimensions are
(Sx-2b-2Nt,Sy-2b-2Nt). Default remaining7x10 gives N10, top x[6,7]/y[3,7],
completion x[6.15,6.85]/y[3.15,6.85], still intersected with legal y[4,6].
Tread heights are h..10h and platform11h: .55m at d0,2.53m at d1.
Changing tile size or tread depth recomputes count, platform, gates, insets and
cache identity; invalid geometry is rejected without clipping.

Per AGENTS resource-safety requirements, count-dependent allocations are checked
before int conversion/np.arange/mesh construction. A private1000-tread per-tile
construction cap rejects unbounded requests with ValueError; approved default10
is unchanged. Extremely small step depths previously could overflow or request
billions of treads. Invalid numeric input also produces contextual ValueError.
This guard is a construction resource limit, not a change to approved terrain
surfaces or difficulty values.

### T04 executed checks and reviews

- RED test initially failed importing missing stair config; implemented then passed.
- Standards review reproduced overflow for step_width1e-309 and malformed numeric
  TypeError; added failing regression then bounded conversion/allocation validation.
  Safe post-fix test also rejects1e-9 without materializing a huge geometry.
- Ordinary plane metadata regression rejects nonhorizontal/wrong-height planes;
  no mismatch between stored planes and generated ordinary tread tops.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: **57 passed**,
  35 existing upstream TorchScript deprecation warnings.
- Targeted `.venv/bin/ruff check` on new/changed terrain, importer and tests: passed.
- `.venv/bin/python -m compileall -q src tests`: passed. Static type checking remains
  unrun because no checker is installed; no packages were changed.
- Installed IsaacLab source still346c74fe722ad371a6c663e3b384b3d172966d11.
- RAM available17–18GiB and GPU7793/8188MiB free checked before each serial run.

```bash
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family stairs --landing --difficulty 1
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family stairs --landing --holes --difficulty 0
```

Both exited0: real platform contact with copied pre-reset success, failed sideways
base-contact landing, runtime tread tensors, entrance and untouched-row partial reset.
Logs: t04-stairs-landing.log and t04-stairs-holes-landing.log. Two environments,
no visualizer, at most55 control steps per run. CPU tests cover all four endpoint/
holes combinations; native runs intentionally sample two complementary combinations.
Controlled platform placement tests the landing contract, not learned stair climbing.

Standards and Spec reviews independently inspected implementation. Standards findings
were fixed; its follow-up was unavailable due model capacity. Spec follow-up reviewed
those fixes and found no remaining concrete defect. Final Verify remains separate.
T05–T12 remain; no commits, pushes or GitHub issue changes/closures.


## T05 / #9 — Implemented; implementation checks passed

User “继续” continued approved Implement. Read current GitHub #9 title/body/comments
(no comments), accepted S65/S66 and ADR-001's horizontal entrance/platform amendment.

### Implemented behavior

- ParkourTiltedStairsTerrainCfg inherits approved count, residual platform, depth,
  rise and holes settings. Only tread planes use z=k*h+(y-5)*tan(15*d degrees).
  Approach stays at0 and platform at(N+1)*h; no entrance ramp or platform tilt.
- Closed plane-topped prisms are used for tilted treads. Flat ground is partitioned
  outside actual tread/platform footprints, preserving negative low-side heights.
  Bottoms close below the minimum prescribed surface; the previous full-tile z0
  slab is not reused for tilted geometry.
- Native count/XY geometry and the single+X route are retained. The first/final
  signed joins may become downsteps; analytic vertical/horizontal rays confirm
  those faces/heights rather than levelling them.
- mirror_sign=-1 reflects canonical geometry AND spawn, legal/completion/support
  regions, gate spans and plane normals/offsets about tile center Y. Canonical
  identity excludes mirror sign; native cache keys still distinguish actual meshes.
  Tests include an asymmetric size10x12/holesTrue sample so unchanged symmetric
  bounds cannot conceal missing metadata reflection.
- Registered implemented-family aggregate adds tilted_stairs with relative weight.2
  and positive training sign. Mirrored configuration is available for matching
  evaluation geometry; final deterministic evaluation entry/wiring remains T12.
  Boxes/gaps/ordinary stairs do not gain mirror options.
- Existing importer provides actual planes/counts and mirror/canonical IDs without
  added learner features. Existing successful-through-platform semantics remain.

Affected code: layouts.py, trimesh mesh/config pair, aggregate imports/config,
registration test, new tilted geometry tests and bounded smoke options. During
editing an accidental mesh-module content overwrite was caught by import tests;
restored existing box/gap/ordinary-stair functions and all regression tests pass.

### T05 executed checks and reviews

- RED test initially failed on the missing tilted config; implemented and passed.
- CPU tests cover both d0/d1, holesFalse/True and mirror signs: exact analytic
  tread/flat heights, negative low side, signed joins, prism winding/closure,
  reflected vertex sets, regions, asymmetric spawn/offsets and cache sample identity.
  Invalid planes, unmatched mirror metadata and wrong mesh/config families fail.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: **74 passed**,
  35 existing upstream TorchScript deprecation warnings.
- Targeted Ruff and `.venv/bin/python -m compileall -q src tests`: passed.
  No static type checker installed; syntax checking is not type checking.
- Installed IsaacLab commit remains346c74fe722ad371a6c663e3b384b3d172966d11.
- RAM available about18GiB; GPU7793/8188MiB free before each serial run.

```bash
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family tilted_stairs --landing --difficulty 1 --tilt-probes
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family tilted_stairs --landing --difficulty 1 --tilt-probes --mirror
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family tilted_stairs --landing --difficulty 1 --tilt-probes --holes
```

All exited0. Logs: t05-tilted-stairs.log, t05-tilted-stairs-mirror.log and
t05-tilted-stairs-holes.log. Each uses two environments/no visualizer and at most
56 control steps. Runs check actual pre-reset platform success, failed base-contact
landing, partial reset/tread tensors and Newton terrain-ray hits on prescribed tops.
All final runs use atol=rtol=1e-5; measured maximum absolute ray errors are
1.9073486e-6m (canonical),1.1920929e-6m (mirror),2.6226044e-6m (holes). The initial
canonical run used an earlier atol1e-4 assertion and was repeated successfully
with the final1e-5 criterion; the latest canonical log supersedes that preliminary
probe. CPU analytic fixtures use1e-7 for all signs/holes/endpoints.

Both independent Standards and Spec reviews found no concrete new defects and
independently ran15 tilted tests (before the final two rejection regressions were
added). Reviewers did not run simulations; native outcomes above were executed by
the primary session. Native probes establish collider surfaces, not indefinitely
stable locomotion or trained climbing. Full evaluation conditions remain T12.
T06–T12 remain; no final Verify stage entry, issue writes, commits or pushes.


## T06 / #10 — Implemented; implementation checks passed

User “继续实施” continued approved Implement. Read GitHub #10 title/body/comments
(no comments), current interfaces/design and accepted ADR-001. S42/S54/S66 define
this family; no extra superimposed tilt or changes to success physics were added.

### Implemented behavior and source changes

- layouts.py: immutable SideSlopeGeometry records the break lines[3,3.5,4.5,5],
  footprint2x2m, transverse center and signed tan(20*d) coefficient. Analytic height
  uses a(x) rising0..1 across3..3.5, constant across3.5..4.5 and falling1..0 across
  4.5..5. Factory supplies gatesx3/5, legal corridor, flat landingx5..7 and0.15m inset.
- trimesh mesh/config pair: closed heightfield with <=0.05m axis grid spacing and
  explicit transition break lines. Flat ground excludes the entire slope footprint,
  so the low half remains below approach elevation. Boundary walls/bottom close
  the mesh; entry/exit heights meet flat ground without adding a lip.
- Exact mirrored surface requires reversing cell diagonals as well as reflecting
  vertices/profile. The mirrored builder changes the transition triangulation to
  match physical reflection. Canonical IDs stay shared while native caches remain
  separate. Asymmetric7x6 tiles test reflected center/spawn/gates/landing at boundaries.
- terrain_importer.py converts profile validity, breaks, local center and signed
  coefficient once to device tensors. No learner observation features added.
- Aggregate/registration now include side_slope at approved relative weight.2.
  Five families are implemented; complete six-family integration remains T12.
- New geometry and common-attempt tests cover endpoints/signs, non-target slope
  support versus far landing, rollback and corridor bypass. Invalid transition
  lengths/gate spans, support planes, profiles and undersized tiles are rejected.

### Mesh error proof and checks

On a transition cell, f(x,y) is bilinear. Mesh interpolation is affine, so their
error has indefinite Hessian and no strict interior extremum. Axis-aligned edges
are exact; along the diagonal the quadratic error reaches its extremum at its
midpoint. All triangle edge midpoints are therefore sufficient for the maximum
absolute error on each cell triangle (plateau error is identically zero).
With |a'|=2, dx,dy<=.05, maximum error is
|tan(20*d)*a'|*dx*dy/4 <= .0004549628m, below approved .001m.
Tests examine every top triangle, not only vertices or random samples. Independent
analytic ray values also verify the envelope itself. Off-grid ray pairs verify
matched mirrors, catching the incorrect same-diagonal reflection implementation.

### T06 executed checks/reviews

- RED tests failed on missing slope config; implemented then passed. A later RED
  metadata regression accepted altered transitions; validation now rejects altered
  transition/corridor/gate contracts and passes that regression.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: **87 passed**,
  35 existing upstream TorchScript deprecation warnings.
- Targeted `.venv/bin/ruff check` over terrain modules and changed tests: passed.
- `.venv/bin/python -m compileall -q src tests`: passed. No static type checker
  installed; syntax check is not static type checking.
- Installed IsaacLab remains346c74fe722ad371a6c663e3b384b3d172966d11.
- RAM available about18GiB and GPU7793/8188MiB free before serial bounded runs.

```bash
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family side_slope --landing --difficulty 1 --slope-probes
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family side_slope --landing --difficulty 1 --slope-probes --mirror
```

Both exited0. Logs: t06-side-slope.log and t06-side-slope-mirror.log.
Two environments/no visualizer, at most58 control steps per run. Actual pre-reset
far-landing success, failed base-contact landing, runtime profile tensors and partial
reset isolation passed. Six native ray probes per run cover both transitions,
plateau and entrance/exit joins, using analytic expected heights and the approved
.001m error limit. Maximum measured errors were .00045585632m (canonical) and
.0004555285m (mirror), including native float32 geometry/ray error.

Standards review found no concrete violations and ran10 slope tests; Spec review
found no concrete defects and ran33 slope/attempt tests before the final metadata
rejection regression was added. Both reviews were read-only and did not execute
simulations. Native probes and synthetic support tests provide bounded correctness
evidence, not learned policy traversal performance. Final Verify remains separate.
T07–T12 remain; no issue writes/closures, commits or pushes.


## T07 / #11 — Implemented; implementation checks passed

User “继续” continued approved Implement. Read current GitHub #11 title/body/comments
(no comments), S43/S44/S49/S66 and accepted ADR-001 native-grid adaptation.

### Implemented behavior and affected source

- layouts.py: RoughGridGeometry stores explicit11-edge X/Y arrays and a read-only
  float64 height matrix[10,10], indexed[X cell,Y cell]. Footprint is exactly
  x[3,5]/y[4,6]; cell width.20m, heights independent U[0,.02+.18*d].
- Local PCG64 sampling is keyed by the SHA256 canonical identity, which includes
  explicit seed, actual sampled difficulty, family, tile configuration and schema.
  A bounded256-entry generation-only memo reuses the same immutable sample when
  layout and mesh hooks request it; cached height-array storage is at most200KiB
  plus small cache overhead. Fresh processes reconstruct the same sample without
  modifying global NumPy RNG state. Native OBJ cache hits regenerate matching
  task metadata; no attempt/reset path resamples heights.
- rough_grid_terrain locally adapts the native box-grid construction pattern.
  Exactly100 closed cells tile the2x2m patch, with positive-volume bases even if a
  sampled top height equals0. No signed heights, extra center platform, intentional
  gaps or tilt/mirror variant. Native `(meshes, origin)` remains intact; task spawn
  is distinct from origin on the far landing.
- terrain_importer.py converts cell edges/heights and grid-valid flags once onto
  env.device. No learner observation features added.
- Aggregate/registration now include all six approved families at weights
  .2/.2/.1/.2/.2/.1. A native CPU-generator test verifies20 columns distribute as
  4/4/2/4/4/2. Final task-wide evaluation/data/curriculum integration remains T12.
- Existing common attempt term handles entry/far gates, retreat/rollback, bypass
  and flat far-landing support. Grid-cell contacts cannot substitute for that
  support; no additional foot/contact reset criteria introduced.

### T07 executed checks/reviews

- RED tests initially failed on missing config; implemented then passed.
- Both d0/d1: all100 downward ray hits match metadata heights; an adjacent rising
  pair has its expected vertical collision face. All101 meshes (ground+100 cells)
  are watertight/positive-volume; no extra central platform masks sampled cells.
- Explicit seeds reproduce the matrix; another seed and another difficulty change
  canonical samples. Global NumPy random state remains unchanged. Cache-on,
  cache-hit and cache-off mesh/layout matrices match at sampled d and placement.
- Invalid shape, nonfinite/negative/above-bound heights, undersized landing space
  and unapproved grid mirror requests fail with contextual ValueError.
- Synthetic attempts isolate far support from grid-cell contacts while base is
  inside completion, plus verify rollback/bypass and both-gate passage.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: **95 passed**,
  35 existing upstream TorchScript deprecation warnings.
- Targeted `.venv/bin/ruff check` on terrain and changed tests: passed.
- `.venv/bin/python -m compileall -q src tests`: passed. No static checker installed;
  syntax checks do not establish static type correctness.
- Installed IsaacLab remains346c74fe722ad371a6c663e3b384b3d172966d11.
- RAM available about18GiB and GPU7793/8188MiB free before serial bounded runs.

```bash
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family rough_grid --landing --difficulty 1 --grid-probes
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --device cuda:0 --viz none --family rough_grid --landing --difficulty 0 --grid-probes
```

Both exited0. Logs: t07-rough-grid-d1.log and t07-rough-grid-d0.log.
Two environments/no visualizer, at most58 control steps per run. Real pre-reset
far-landing success, failed base-contact landing, partial reset and runtime matrix
shape/mask checks passed. Repeated manual resets preserve the full generated height
table. Corner and central-cell native collider probes match metadata with maximum
errors4.7236681e-6m(d1) and2.6635826e-6m(d0), within atol=rtol=1e-5.
These controlled placements prove bounded data/collider/landing behavior, not a
trained policy's ability to traverse the rock patch. This remains the approved
box-grid approximation, not natural-rock morphology or a paper-performance claim.

Independent Standards and Spec reviews each ran32 targeted tests and found no
concrete defect. Spec's stale aggregate comment was corrected to reflect current
six-family weights. Reviewers did not rerun simulations. T08–T12 remain; no final
Verify stage entry, GitHub issue writes/closures, commits or pushes.


## T08 / #12 — Implemented; implementation checks passed

User “继续” continued approved Implement. Read GitHub #12 title/body/comments
(no comments), current proprio/action/command contracts, and installed native
ObservationManager, CircularBuffer, SceneEntityCfg, JointPositionAction and
ManagerBasedRLEnv/Env step/reset source. No replacement sampler or RL loop added.

### Implemented behavior

- parkour_env_cfg.py: canonical noisy proprio history is now5x42=210, chronological
  time-major. Native history stores one noise sample per term/observation, and first
  append after reset backfills identical copies. No extra clipping/scaling or gravity
  normalization. Commands stay a separate3-vector; no command/action noise added.
- Joint observation/gain selectors explicitly preserve canonical FL/FR/RL/RR and
  hip/thigh/calf order, matching official JointPositionAction. Official scale.5,
  default-pose offset and clip=None remain; nominal Go2 actuator model/limits unchanged.
- Initial UniformVelocityCommand now disables heading conversion/forced standing
  and uses20.02s resampling period, exceeding approved20s attempts. Per-family
  curriculum bounds/minimal command sampler remain T11; this does not claim T11.
- New project validate_parkour_actions(env, actions) checks finite float32[N,12],
  exact shape/device and Tensor input before simulator submission, without coercion.
  It is an explicit verification/untrusted-input boundary, not automatically added
  to every native step. Native env.step still permits device transfer and some
  broadcasting if callers bypass this check. GPU finiteness checks synchronize the
  host, so trusted hot-path behavior is preserved. Interfaces.md documents this
  interpretation of the approved “failure in checks” requirement.
- Manual partial-reset native behavior is documented: selected rows clear/backfill,
  non-reset rows retain four frames and append one new observation, even without
  a physics transition. Read-only compute(update_history=False) does not append.
  No extra terminal observation/history/critic/AMP snapshots introduced.

Affected files: registered environment configuration, mdp/actions.py and lazy export,
CPU/native proprio tests, interfaces.md and issue-local status/implementation logs.

### T08 executed checks/reviews

- RED tests initially failed on missing action check; implemented then passed.
- CPU tests construct the installed native ObservationManager with an external
  simulator-boundary fixture whose joint names are intentionally reversed. Verify
  exact feature/time order, noise ranges, same reset frame repeated5x, raw action
  history, shared consumer views, selected reset and read-only history reads.
- Shape/rank/batch, nonfinite, dtype/non-Tensor and wrong-device checks reject
  invalid actions before submitting them. Finite values outside[-1,1] are accepted.
  Config tests check no extra scale/clip/corrupted groups and canonical foot mapping.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: **109 passed**,
  35 existing upstream TorchScript deprecation warnings.
- Scoped Ruff over new action utility/export stub and tests: passed. The full legacy
  parkour_env_cfg.py still has pre-existing import/format warnings; only affected
  added long selector lines were wrapped, avoiding unrelated cleanup.
- `.venv/bin/python -m compileall -q src tests`: passed. No static type checker is
  installed; syntax checking does not replace type checking.
- Installed IsaacLab remains346c74fe722ad371a6c663e3b384b3d172966d11.
- RAM available about18GiB and GPU7793/8188MiB free before bounded native execution.

```bash
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_proprio_smoke.py --device cuda:0 --viz none
```

Exit0, log t08-proprio-actions.log. Two environments,2x1 box tiles, no visualizer,
only4 physical control steps. cfg.seed=7 makes the native noise test reproducible.
The script verifies actual proprio[2,210], commands[2,3], canonical names through
native action IO descriptor, affine target processing including action2 without a
physics step at that target, raw actions, chronological history, noise bounds,
selected reset and actual timeout autoreset. Returned done-row history backfills
new-episode state/raw zero actions; non-reset row history retains prior frames.
No final_obs export. Bad inputs are rejected by the explicit check, never forwarded
to physics. Motor saturation/learned policy performance are not asserted by this test.

Standards and Spec reviews independently ran12 initial tests and found no concrete
defect; reviewers did not execute native smoke. Later read-only-history and foot-map
regressions bring the proprio CPU file to14 tests, also passing in the full suite.
Spec review confirmed optional validation matches approved “in checks” wording;
validation is not misrepresented as automatic enforcement by env.step. Both the
native script and config already use fixed seed7 for noise assertions.

T09–T12 remain. Privilege feature expansion/reward alignment, held low-rate sensor
adapters, curricula and final evaluation/integration are still incomplete. No final
Verify stage entry, issue writes/closures, commits or pushes.

## T09 / #13 — Native depth/height adapters and capture metadata

Implemented `labs/sensors/{camera,camera_cfg,height_scanner,height_scanner_cfg,sample}.py`
with native lazy exports. Camera calibration: xyzw(.5,-.5,.5,-.5), ROS optical axes,
position(.30,0,.05), HFOV87 degrees, square pixels, centered intrinsics, .1–5 m
image-plane depth. Scalar capture hook copies/sanitizes only legitimate native rows
into owned storage; native batch eligibility is disabled. Scanner registers foot
reference and base-heading sites before finalization, composes persistent Warp
poses, and retains native query graphs/clocks/reset behavior. All grids are xy/X
fastest; reference-Z heights exclude the2 m launch offset, reach5 m. Body/four-foot
captures .1 s; critic .02 s; debug readers disabled. `read_low_rate_targets` checks
capture/reset alignment and spatial/metadata shape,dtype,device contracts. Target
keys are preserved; metadata supplies masks, episode IDs, capture times and ages.

TDD: calibration test initially failed import, then passed. Bundle tests initially
failed import, then passed; malformed mask rejection tests added after review.
Native command, exit0, log `t09-sensors.log`:

```bash
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_sensors_smoke.py --device cuda:0 --viz none
```

Two environments, five ordinary control steps plus pose-only analytic checks:
shape/dtype/masks, calibrated wall depth, base-yaw foot grids, world-down reach,
reference-Z heights, held values, distinct post-reset clocks, identity and row
isolation passed. A second test-only camera has the same optics at x=.60 m;
60,048 visible wall samples match .90 m within2e-4 m and provide nonzero held
samples for partial-reset isolation. Production pose remains x=.30 m.

**Material review item:** the production camera is entirely self-occluded in the
upright tested pose: raw center depth .022564 m, all sanitized pixels zero/invalid.
The independent calibration camera proves optics/adapter behavior, not useful
terrain visibility from production placement. No approved pose or renderer
visibility policy was silently changed. A mount/visibility change needs a separate
specification decision after this implementation handoff.

Diagnostic runs initially exited1 for a smoke-script metadata field name, then for
an assumed clear central view. An intermediate run overlapped config integration
and exposed the now-removed airtime `command_name` parameter. These were fixed;
there is no claim those diagnostic runs passed. The final command above exited0.

## T10 / #14 — Applied dynamics, clean data and S67 rewards

Added native startup independent joint P/D multipliers U[.8,1.2]. Existing native
mass log-uniform scaling, COM offsets and shared material writes are retained and
read back; Newton uses one friction coefficient. No startup redraw occurs on reset.
No push or substitute zero-force event remains. Privilege is273 features: eight
latest thigh/calf flags, D then P, applied COM/mass/material and clean state/critic
heights. AMP exports current named clean fields, canonical joints/feet and explicit
xyzw -> public wxyz conversion. All-invalid critic data yields zero height and
false validity, suppresses height contributions and creates no reset condition.

Corrected stance to approved Euler roll/pitch and four-foot/low-command gate;
height penalty uses mean valid critic terrain; orientation uses roll²+pitch²;
leg collision uses four-substep normal-force history; airtime has no command gate
or nonnegative clamp; second action differences start immediately from zero and
clear selected rows only. Native RewardManager applies the only dt scaling.

`tests/test_parkour_rewards.py` checks every S67 raw term and weight against numeric
fixtures and executes native RewardManager for dt-once verification. Separate cases
cover invalid heights, latest-vs-history contact, negative low-command airtime,
Euler orientation, first actions and partial reset. First imports failed before
implementation; all final cases pass.

## T11 / #15 — Independent curricula and native fixed-attempt sampler

One native curriculum owner reads ending flags directly before native reset;
there is no record queue/consumed flag/second episode scheduler. Terrain windows
last100/min20 use family+level buckets. Speed batches use20 >=1 s attempts with
actual-duration-normalized tracking integrals, equal attempt weights including
failures, and .1 steps within[1,3]. Endings process in ascending env ID. Only ending
rows migrate; highest promotion chooses a lower level excluding top. Single-level
cases remain0. Manual/initial resets do not count; windows/batches/bounds persist.

Minimal CommandTerm uses native reset/countdown with20.02 s period for20 s episodes,
family-specific bounds, vy/yaw0 and no heading/standing overrides or metric owner.
Sampler reads the owner through public `curriculum_manager.cfg.terrain_levels.func`
(the pinned CurriculumManager has no get_term_cfg method). It samples only after
new assignment; a current attempt's command stays fixed. Native init order creates
CommandTerm before curriculum, but no sampling occurs until all managers exist.
Float32 numeric boundary allowances are1e-6 s for exactly50 intervals and1e-7 for
inclusive speed-score thresholds; no physics interval or acceptance limit changed.

`tests/test_parkour_curriculum.py` covers min20, inclusive.8/.3, hold regions,
rolling100, highest recycle/single row, family isolation, sorted simultaneous
endings, short attempts, equal-duration weighting, failure inclusion, clearing,
clamps, invalid bounds and1000 native countdown updates without command changes.
A .3 score fixture first failed due float32-to-Python threshold conversion; inclusive
numeric comparisons fixed it. Final tests pass.

Combined T10/T11 native command, exit0, log `t10-t11-dynamics.log`:

```bash
timeout --kill-after=10s 180s .venv/bin/python tests/parkour_dynamics_smoke.py --device cuda:0 --viz none
```

Two environments,51 control steps: read applied native controller gains, mass,
COM and per-shape material bindings; compare all clean groups/canonical feet;
confirm unchanged startup parameters across reset; trigger timeout at exactly50
physical transitions; pre-reset stats include ending step, promote row0 before
spawn/next-command reset and retain row1; all-invalid height contributes zero
without termination. All assertions passed.

## User feedback — IsaacLab terrain lazy-import structure

`labs/terrains/trimesh/__init__.py` now only invokes native `lazy_export()`;
`__init__.pyi` declares six configuration exports. Aggregate config imports through
that boundary. `mesh_terrains_cfg.py` also matches native IsaacLab3.0: functions
are `{DIR}.mesh_terrains:name` strings, converted by native configclass into callable
ResolvableString objects. No eager implementation import remains in configuration.
A fresh interpreter confirms package import loads no config/mesh; resolving and
constructing all six configs still loads no mesh implementation; invoking the
first configured function imports it. Existing function-call and cache tests pass.

## T12 / #16 — Complete aggregate, deterministic evaluation and integration

`PARKOUR_TERRAINS_CFG` is the six-family aggregate; implementation-era export stays
an alias. Default10x20 grid/initial0..5/4,4,2,4,4,2 allocation retained. Native
curriculum changes only row, keeping family; stairs/tilted-stairs have distinct IDs.

`configure_parkour_evaluation`/`make_parkour_evaluation_cfg` in Unitree/evaluation.py
select family/level/command/mirror/seed, disable curricula/noise/startup randomization,
use nominal resets and read authored shared material. Startup fixed-level assignment
precedes first reset. Generator retains native ten-level difficulty strata while
adaptive assignment is off. Registry adds `eval_env_cfg_entry_point`; `play_mode`
uses deterministic defaults. Same seed/family/level mirror pairs share canonical
IDs and sampled difficulty. `docs/parkour.md` documents use/data, applied rewards,
paper/Go2 adaptations, ownership, camera limitation and consumer boundaries.

Serial evaluation commands each use the following template (2 envs, six physical
control steps, plus pose-only scan probes and optional wrapper check):

```bash
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_evaluation_smoke.py --family FAMILY --level 9 --mirror SIGN --device cuda:0 --viz none
```

Nine final cases exited0: box(+`--wrapper`), gap, stairs, tilted_stairs signs+1/-1,
side_slope signs+1/-1, rough_grid, and stairs(+`--endpoint`). Exact command arrays,
resource checks and exit codes for the latter eight are in `t12-eval-results.json`;
box command is the template with FAMILY=box,SIGN=1 and`--wrapper` (log
`t12-eval-box.log`). One initial stair fixture failed because a NumPy center became
float64; corrected to float32, reran successfully. Manifest retains that failed
attempt followed by its passing correction. No criterion was weakened.
Endpoint stairs platform2.53 m is within the approved scanner reach; center height
.4 m matches within1e-5 m. Nominal reset states and clean observations reproduce
exactly, metadata keys/dtypes hold, and no adaptive assignment occurs. Canonical
comparison of nine logs confirms both mirror pairs; `t12-canonical-pairs.json`.

Current full stack contact/geometry reruns also exited0, using:

```bash
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py FLAGS --device cuda:0 --viz none
```

FLAGS are recorded exactly in `t12-contact-results.json`: tilted_stairs d1 with
landing+tilt probes, its mirror; side_slope d1 with landing+slope probes, its mirror;
rough_grid d1 with landing+grid probes; gap with landing+floor/wall contacts.
Geometry-only probe placement was updated to stay within the newly implemented5 m
ray reach, rather than leaving the old4 m reference plus2 m launch beyond range.
Each run passed real target-support landing and sideways base-failure checks.
Low-side tread/upper-last-tread, slope transitions/joins (<.001 m), grid cell tops
and gap floor/wall non-success checks passed on the final sensor/dynamics stack.

Native RSL-RL wrapper check passed nested TensorDict groups, done-row new-episode
capture metadata, done merge and`time_outs`. It does not create terminal snapshots
or solve learner bootstrap. Existing runner's missing`policy` group/model-input
assembler remains outside environment-only scope and is explicitly documented.

## Final implementation checks and independent review

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: exit0,
  **141 passed**,35 upstream TorchScript deprecation warnings; `pytest-final.log`.
  Reran after final terrain lazy-function change; no test failure remains.
- `.venv/bin/python -m compileall -q src tests`: exit0.
- Scoped `.venv/bin/python -m ruff check` over new sensor/command/curriculum/eval
  modules, changed MDP modules/exports, lazy terrain exports/aggregate and new
  tests/smokes: exit0. Legacy parkour_env_cfg formatting/import issues predate this
  work; no claim that an unscoped repository-wide Ruff run passed.
- Native final successful cases:17 (T09 + combinedT10/T11 +9 evaluation +6 contact
  cases). Each run checked RAM/VRAM first, used2 envs/no visualizer, timeout150 s
  (combined dynamics180 s), serial processes. Free VRAM7793/8188 MiB, available
  RAM >18 GiB at checks; no OOM/resource instability observed.
- No mypy/pyright/basedpyright installed (checked import availability); static
  typechecking was not run. Compileall is syntax/import compilation, not typing.
- Standards review found stale leg naming/docs and unused stance scanner argument;
  fixed. Spec review found missing mask validation; fixed with rejection tests.
  Both independent reviewers rechecked and report no remaining concrete findings.
- Fixed-point review used HEAD bc3373a1ff340eeeb7e3760e7a95109f90ffcf35 plus scoped
  tracked/untracked working changes; no new commits exist. Pre-existing deleted
  files/AGENTS changes were excluded. No commit/push or GitHub edits/closures.

All tickets' implementation work is ready for unified user review. Final Verify
stage has not begun. Production camera visibility needs a subsequent user decision;
TODO-01 depth noise and TODO-02/03 deferred backends remain outside approved scope.


## User geometry correction — 2026-11-06

User authorized equal Y widths for holes=True stair treads/platforms and an
unblended transverse planar ramp (ordinary ramp rotated 90°). ADR-008 supersedes
the earlier conflicting width/transition details. Implemented layout/mesh,
regions, cache revision, regression tests and native probe expectations; see
verification.md for executed checks. Other geometry parameters remain unchanged.


Ground-aligned slope follow-up (2026-11-06): user approved the current angle/joins
and requested minimum height z=0. Updated analytic heights, prism, cache revision
3 and regressions; 159 tests and native slope probe passed. Camera mount .35 m
was user-modified and visibility user-confirmed; synchronized documentation/test
expectation without further mount edits. See verification.md.
