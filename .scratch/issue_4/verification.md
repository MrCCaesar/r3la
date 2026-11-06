# Issue #4 — Verify report

Status: **Current checks passed; unified user acceptance pending.** Verify was
authorized on 2026-11-06. Earlier failures/limitations below are historical unless
explicitly retained by the latest follow-up.

## Pre-commit check — 2026-11-06

User authorized cleanup and commit. Removed 14 completed publication helper/body
files and disposable local caches; retained decision history and verification logs.
`PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q -p no:cacheprovider`
passed: **159 tests**, 35 upstream warnings (`verify-precommit.log`).
`git diff --check` passed. No native simulation was repeated for cleanup alone.

## Ground-aligned slope and camera confirmation — 2026-11-06

User confirmed the existing slope angle/joins, requested the lowest edge at ground
level, and reported self-occlusion resolved after moving the camera. Current
camera config is (.35,0,.05); its mount assertion and current documentation were
synchronized without altering the user's setting. Camera visibility resolution
is user-confirmed; no new camera visibility measurement was performed this turn.
The former x=.30 m visibility blocker is closed on that evidence.

The slope now uses z=(y-4)*tan(theta), mirrored as z=(6-y)*tan(theta), preserving
angle, footprint and direct joins. Mesh and analytic queries share the new datum;
geometry cache revision is 3. Staircase geometry is unchanged.

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: **159 passed**,
  35 upstream warnings. Log: `verify-ground-aligned-slope.log`.
- `.venv/bin/python -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- `timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --family side_slope --slope-probes --difficulty 1.0 --device cuda:0 --viz none`:
  **passed**, two environments, no visualization; available RAM 17,247 MiB and
  free VRAM 7,793 MiB checked before execution. Native maximum surface error
  2.3841858e-07 m; task tensors/partial reset checks passed. Log:
  `verify-ground-aligned-slope-native.log`.

New CPU cases verify zero low-edge height and nonnegative walkable top for d=0,
.5,1 and both mirror signs. This does not claim that the entire historical native
matrix was rerun against the latest tree. No training or commit/push performed.

## Camera debug outputs — 2026-11-06

User requested RGB and other native camera outputs for debugging. Removed the
project-only exact-list restriction while retaining required image-plane depth.
Extras use native Camera allocation/validation and buffer lifetime; training
samples, default configuration, calibration and supported backend are unchanged.

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: **153 passed**,
  35 upstream warnings. Log: `verify-camera-debug-pytest.log`.
- `.venv/bin/python -m compileall -q src tests` and `git diff --check`: passed.
- `timeout --kill-after=10s 150s .venv/bin/python tests/parkour_sensors_smoke.py --debug-outputs --device cuda:0 --viz none`:
  **passed**, 2 environments, available RAM 17,813 MiB and VRAM 7,793 MiB checked
  first. All ten requested native output keys/shapes were present; RGB, normals
  and colored semantic segmentation dtypes checked. Existing calibrated depth,
  10 Hz holds, partial reset and renderer-write isolation checks passed.
  Log: `verify-camera-debug-native.log`.

No additional renderer backend was added. Production camera self-occlusion is
unchanged; enabling RGB helps inspect it but does not correct the mount.

## Geometry revision verification — 2026-11-06

User-directed correction implemented per ADR-008: holes=True treads and platform
share Y width in both stair families; the side slope is a single transverse plane
with direct joins. Layout/support/completion/gates, native importer breakpoint
shape (rows, columns, 2), mesh cache revision and tests were synchronized.

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`:
  **143 passed**, 35 upstream warnings; `verify-geometry-revision.log`.
- `.venv/bin/python -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- `timeout --kill-after=10s 150s .venv/bin/python tests/parkour_box_smoke.py --family side_slope --slope-probes --difficulty 1.0 --device cuda:0 --viz none`:
  **passed**, 2 environments, serial, available RAM 17,541 MiB and VRAM 7,793 MiB
  checked before rerun. Native plane/direct-join maximum height error
  2.3841858e-07 m; task tensors and partial reset passed. Log:
  `verify-slope-revision-native-rerun.log`.
- Initial native attempt failed on an obsolete 4-breakpoint test assertion; its
  log is retained as `verify-slope-revision-native.log`. Updated that assertion
  and the importer's non-slope placeholder to 2 entries before the passing rerun.

CPU tests cover equal-width collision boundaries, both difficulty endpoints,
mirrors, watertight surfaces and cache reuse. Earlier native stair simulations
were not repeated against this revision. Production camera self-occlusion remains
unresolved, so these results do not constitute overall acceptance.

## Follow-up — debug visualization correction

User removed the explicit FL `debug_vis=True` override. Targeted verification:
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_parkour_sensors.py`
returned **6 passed**, 35 upstream warnings. The debug-setting failure below is
resolved; the full suite was not repeated in this follow-up. Production camera
visibility remains unresolved. No scanner implementation changes were made.

## Current working-tree verification — 2026-11-06

Confirmed facts:

- Initial collection/native startup failed on an unmatched `]` in
  `parkour_env_cfg.py`'s commented visualizer configuration. The closing bracket
  was commented to match the surrounding disabled block; no runtime configuration
  was changed by this repair.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`:
  **140 passed, 1 failed, 35 upstream TorchScript deprecation warnings**.
  Evidence: `verify-pytest.log`.
- Failed test:
  `tests/test_parkour_sensors.py::test_configured_grids_have_approved_order_reach_periods_and_no_debug_readers`.
  Current FL scanner sets `debug_vis=True`, contrary to the approved no-extra-debug-readers
  contract. The current setting was preserved and the assertion was not weakened.
- `.venv/bin/python -m compileall -q src tests`: passed after the syntax repair.
- `git diff --check`: passed.
- Three current native integration checks passed, serially with two environments,
  CUDA device 0, no visualization, and bounded timeouts:

```sh
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_sensors_smoke.py --device cuda:0 --viz none
timeout --kill-after=10s 180s .venv/bin/python tests/parkour_dynamics_smoke.py --device cuda:0 --viz none
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_evaluation_smoke.py --family box --level 9 --wrapper --device cuda:0 --viz none
```

Evidence: `verify-sensors.log`, `verify-dynamics.log`, `verify-wrapper.log`, and
`verify-native-results.json`. The manifest retains the initial failed sensor attempt;
its log path was overwritten by the successful rerun. RAM/VRAM were checked before
every process (minimum available RAM 18,561,980 KiB; free VRAM 7,793 MiB).
Sensor cadence/reset isolation, native dynamics/privilege and terminal curriculum
updates, and TensorDict/timeout forwarding passed. This is not a training run.

Open items and recommendation:

1. Resolve the FL scanner debug setting against the approved contract, then rerun
   the failed regression. Treat the current flag's intent as unconfirmed.
2. Historical native evidence shows the approved production camera mount is fully
   self-occluded in the tested upright pose. The passing independent camera fixture
   validates calibration, not production visibility. Decide a physical mount or render
   visibility specification change before implementation; no change was made here.

The earlier 141-test and broader native matrix below are historical implementation
evidence, not a substitute for the current 140-pass/1-fail result. No claim is made
that all earlier native scenarios were repeated against this working tree.

## Historical implementation evidence — 2026-11-05

The following records were collected before final Verify was authorized.

## Confirmed environment and limits

- Python: repository `.venv/bin/python` for every check.
- IsaacLab source: `346c74fe722ad371a6c663e3b384b3d172966d11`, unchanged dependency tree.
- Supported combination: Newton MJWarp + Newton Warp renderer only.
- Package metadata: isaaclab42.0.0, isaaclab-newton11.0.0, Newton1.8.0.dev0,
  Warp1.17.0, Torch2.11.0+cu130, TensorDict0.14.3.
- Simulations serial,2 environments, `--viz none`, bounded150 s per process
  (combined dynamics180 s). RAM/VRAM checked before every process; available
  RAM>18 GiB and free VRAM7793/8188 MiB. No exhaustion/instability observed.
- Static typing tools were unavailable; compileall does not replace typechecking.

## Acceptance trace and evidence

| Contract / ticket | Implementation evidence | Limits / result |
| --- | --- | --- |
| T01/#5 layout, generation/cache, placement/reset | `test_parkour_terrain.py`, `test_registration.py`, T01 logs and implementation history | Pass; deterministic layout/mesh/cache parity, distinct origin/spawn, full conservative footprint |
| T02/#6 ordered gates, landing, failure precedence | `test_parkour_attempt.py`, T02 logs; current six contact runs | Pass; finite criterion and aggregate contact-point limitations retained |
| T03/#7 gap | `test_parkour_gap.py`, `t12-gap-contacts.log` | Pass; landing success, failed sideways landing, floor and wall physical contact rejected as success |
| T04/#8 stairs | `test_parkour_stairs.py`, earlier holes run, `t12-eval-stairs*.log` | Pass; N10, residual1x4 platform, maximum2.53 m platform ray within5 m reach |
| T05/#9 tilted stairs/mirror | `test_parkour_tilted_stairs.py`, current tilted-stairs probe/eval logs | Pass; negative low-side surface and high final tread preserved; canonical mirror identity |
| T06/#10 side slope/mirror | `test_parkour_side_slope.py`, current slope probe/eval logs | Pass; transition/join errors below.001 m, canonical mirror identity |
| T07/#11 rough grid | `test_parkour_rough_grid.py`, current rough-grid probe/eval logs | Pass; fixed100 cell heights, real tops and target support |
| T08/#12 history/actions | `test_parkour_proprio.py`, `t08-proprio-actions.log` | Pass; canonical210 history, noisy backfill/partial reset, affine action target; strict input checker explicit rather than injected into native step |
| T09/#13 depth calibration/data | `test_parkour_sensors.py`, `t09-sensors.log` | Adapter/axes/units/masks pass; independent x=.60 m fixture wall.90 m; production x=.30 m view entirely self-occluded in tested pose |
| T09/#13 clocks/reset/scans | same tests/log and final eval stack | Pass;10 Hz hold,50 Hz critic, base yaw with foot translation, capture-time reference Z, shape/dtype/device checks, partial-reset isolation |
| T10/#14 applied dynamics | `t10-t11-dynamics.log` | Pass; actual gain/mass/COM/material readback, startup persistence, no pushes |
| T10/#14 clean privilege/AMP | same native log + reward/sensor fixtures | Pass;273 features, D then P, eight ordered contacts, AMP wxyz/feet and height validity |
| T10/#14 all16 S67 rewards | `test_parkour_rewards.py`, native RewardManager fixture + combined native log | Pass; each raw formula+weight, dt once, first/second action startup, negative low-command airtime, history/latest difference, all-invalid height zero/no reset |
| T11/#15 curricula/commands | `test_parkour_curriculum.py`, `test_parkour_attempt.py`, combined native log | Pass; thresholds/window/batch/duration/sorting/isolation, ending physics step, migration before spawn and command, no current-attempt resampling |
| T12/#16 allocation/evaluation | registration/evaluation tests, nine current eval logs | Pass; default columns4/4/2/4/4/2 and initial0..5; fixed family/level/command, nominal parameters/no noise/no jitter, adaptive assignment off |
| T12/#16 consumer boundaries | native RSL-RL wrapper in box eval | TensorDict nested groups, dones and timeout forwarding pass; downstream model/runner/bootstrap not implemented |
| Terrain lazy imports (user feedback) | fresh-process import/call check +141-test final suite | Pass; package and config imports defer mesh implementation until first function invocation, matching native ResolvableString pattern |

S67's16 rows are all exercised by `test_all_s67_raw_terms_weights_and_native_dt_once`;
other reward fixtures cover branch/startup/partial-reset cases. Acceptance rows are
not redefined to compensate for failures.

## Exact commands and outcomes

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_sensors_smoke.py --device cuda:0 --viz none
timeout --kill-after=10s 180s .venv/bin/python tests/parkour_dynamics_smoke.py --device cuda:0 --viz none
timeout --kill-after=10s 150s .venv/bin/python tests/parkour_evaluation_smoke.py --family box --level 9 --wrapper --device cuda:0 --viz none
```

All above exit0. Final pytest: **141 passed**,35 upstream deprecation warnings,
3.23 s (`pytest-final.log`), rerun after final lazy-function configuration changes.
Plugin auto-loading is disabled because an unrelated ROS plugin lacks `lark`.
Scoped Ruff exit0; exact scope is in implementation.md. Legacy config lint is
not presented as a passing repository-wide lint run.

The other eight eval command arrays and exit codes are in
[t12-eval-results.json](t12-eval-results.json); all latest cases exit0. Six final
geometry/contact command arrays and resource records are in
[t12-contact-results.json](t12-contact-results.json); all exit0. These use
`parkour_box_smoke.py` with approved landing/probe/contact fixtures and final
sensor/dynamics configuration. No simulations ran concurrently.

[t12-canonical-pairs.json](t12-canonical-pairs.json) captures nine final evaluation
records: box,gap,stairs,tilted_stairs±,side_slope±,rough_grid,stairs endpoint.
Both mirror pairs share canonical ID and actual difficulty. The exact d=1 fixture
reports platform2.53 m and center ray height.4 m. It is distinct from ordinary
level9 evaluation with actual deterministic sampled difficulty below1.

There were failed intermediate diagnostics: mistaken test field name, production
self-occlusion assumption, stale airtime parameter during integration, and one
float64 test-position fixture. Corrections and outcomes are recorded in
implementation.md. The eval manifest retains the failed dtype attempt and its
successful rerun. No claim that these failed attempts passed is made.

## Independent review

Standards and Spec reviewers examined scoped tracked/untracked changes against
HEAD `bc3373a1ff340eeeb7e3760e7a95109f90ffcf35`. Earlier user changes and prior
implementation slices were excluded from this continuation's scope.

- Standards: stale contact naming/docs and unused stance scanner selection fixed;
  recheck reports no remaining concrete findings.
- Spec: missing mask shape/dtype validation fixed with rejection tests; recheck
  reports no remaining concrete findings and14 sensor/evaluation CPU tests passed.

## Assumptions, open review items and next stage

The accepted finite landing window does not prove indefinite stability. Contact
points are force-weighted native aggregates. Bounded controlled placement validates
environment correctness, not policy ability or learning performance.

**Camera visibility needs user review:** every production pixel is invalid from
self-occlusion in the tested upright pose. It correctly follows the approved mount
and invalid encoding. The independent camera proves calibration; it does not meet
the practical need for visible terrain at the approved mount. A physical mount or
render visibility policy change requires a new explicit design decision. No such
change has been made.

No open implementation task remains in T01–T12. Final acceptance remains pending.
TODO-01 depth noise and TODO-02/03 additional backends retain their approved
deferred status. Existing runner configuration references a missing policy group
and lacks the SWAP assembler; learner work is outside scope. Timeout bootstrap
needs a consumer decision because terminal snapshots are intentionally absent.

Historical handoff: unified review and Verify authorization were pending at that time.
Verify is now authorized and its current result is recorded above. No commit/push,
issue edit or closure has been performed.
