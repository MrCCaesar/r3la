# Issue #4 — Performance implementation verification

Status: **T13–T16 implemented; implementation validation passed.** User invoked
implement for the approved tickets. No user acceptance or GitHub closure implied.
The invoked implement skill authorizes review and local commit of this work.

## Outcome

| Metric, median of five window means | Original | Final production | Reduction |
|---|---:|---:|---:|
| Full step | 34.3336 ms | 13.7804 ms | 59.86% |
| Actual complete observation compute | 28.8039 ms | 8.2540 ms | 71.34% |

Both exceed the approved30% runtime reduction target. Thresholds remain step
<=24.0335116767ms and observations<=20.1627250047ms. Final production benchmark
used unpatched --variant baseline (default), NOT the research fused injection.
Its JSON commit field identifies precommit HEAD5768061; production code was the
modified working tree. performance-production-source-hashes.json identifies the
exact implementation sources used. The local delivery commit will include them.

Configuration: four environments, RTX4060 Laptop, native Newton/Warp, seed7,
zero residual actions, RGB+depth,10x20 six-family scene;50 warmup steps followed
by5x100-step windows per metric. Full-step windows synchronize only at boundaries;
observation timing is a separate phase inside real steps. Raw windows/categories
and5 partial-reset samples are in performance-production.json. Full-step window
means range13.2681–14.4904ms; every window is below the acceptance threshold.

The full-bundle function is called zero times by final observation selectors
(diagnostic30 observations), compared with16 per observation originally. Six
samples are still freshly validated for each selector; no persistent cache or
extra sensor scheduler is introduced. No promise of fewer physical captures is
made. Fields retain borrowed storage; native manager output/history ownership is
unchanged. One host-visible combined alignment decision replaces15 successful
individual GPU decisions; failure diagnostics preserve original ordering.

## Executed tests and native checks

- T14 red-before-green: new public selector test initially failed because it
  called the full bundle assembler; after direct field selection it passed.
  Log: performance-t14-red.log. Initial sensor module16 passed, final25 passed.
- T15 red-before-green: new direct termination import/export test initially
  failed on missing module; relocation then passed. Log: performance-t15-red.log.
  Attempt/curriculum targeted suite40 passed. Relocated class is byte-identical
  to original; only its path and import consumers changed.
- T13 performance red is the measured original baseline exceeding the approved
  thresholds. Structural and alignment behavior tested before/after optimization.
- Independent baseline differential: check_fused_prototype.py now loads original
  code with git show5768061, compares FINAL PRODUCTION read_low_rate_targets,
  and passes180 cases, including shape/dtype/device, first episode rank,
  capture eligibility, equal infinities, NaN, tolerance and error precedence.
  Log: performance-production-equivalence.log.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`:
  **169 passed**,35 upstream TorchScript deprecation warnings.
  Log: performance-production-pytest.log.
- `.venv/bin/python -m compileall -q src tests`: passed. `git diff --check`: passed.
  Neither pyright nor mypy is installed in this environment; static typechecking
  was not run. Compileall is not a substitute for typechecking.
- Native serial sensor check (two envs):
  `timeout --kill-after=10s 150s .venv/bin/python tests/parkour_sensors_smoke.py --debug-outputs --device cuda:0 --viz none`
  passed: RGB/debug outputs, known wall depth, foot frame geometry,10Hz holds,
  50Hz critic, same-step partial reset and renderer-write isolation.
- Native dynamics/curriculum (two envs):
  `timeout --kill-after=10s 180s .venv/bin/python tests/parkour_dynamics_smoke.py --device cuda:0 --viz none`
  passed: parameters/privilege/AMP, termination ending step, pre-reset curriculum.
- Final production benchmark (four envs):
  `timeout --kill-after=10s 240s .venv/bin/python .scratch/issue_4/benchmark_performance.py --result .scratch/issue_4/performance-production.json --device cuda:0 --viz none`
  passed. Exact commands, resource checks, exit codes and log paths recorded in
  performance-production-native.json; resources checked before each process.

Initial sensor run failed on a historical assertion requiring all production
pixels to be invalid at the old camera mount. Corrected the fixture for the
already user-approved .35m mount: require visible pixels and compare full depth
and mask encoding against raw native depth/range. Independent .60m calibration
wall remains unchanged. Initial failure log retained; all three reruns passed.

## Code review

Review baseline5768061 against working tree; two independent read-only axes per
code-review skill. Standards found stale current-state documentation, now fixed.
Spec found missing structural-error differential cases, now expanded and executed.
Both reviewers rechecked and reported no remaining findings. Reviews do not
replace the executed tests or imply user acceptance.

## Scope and limits

All4 new tickets delivered locally; GitHub issues were not edited or closed.
Public mdp.ParkourAttemptState points to the sole terminations implementation;
old mdp.attempts is removed as approved. Current src/tests have no old imports.
Four-env zero-action measurements are not training-scale throughput or traversal
coverage of all six families. Active columns[0,4,9,14] cover four families while
the full six-family scene remains. One natural reset in observation windows is
reported separately from5 explicit partial resets. No full training or upstream
edit. User review remains the next handoff; local commit required by implement.
