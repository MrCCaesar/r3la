# Issue #4 — Performance implementation verification

Status: **Formal Verify passed**; latest results are in the section below.
Historical implementation stage: T13–T16 implemented; implementation checks passed. User invoked
implement for the approved tickets. No user acceptance or GitHub closure implied.
The invoked implement skill authorizes review and local commit of this work.

## Formal Verify — 2026-11-06

Status: **PASS for approved performance follow-up criteria A1–A7.** User explicitly
requested “进入verify”. Verified commit cbd642388c995174b91838b79ea658fc62b54bca;
production tree was clean at entry. No production changes were needed.

| Metric | Original baseline | Current commit Verify | Reduction |
|---|---:|---:|---:|
| Full step median window mean | 34.3336 ms | 13.3510 ms | 61.11% |
| Complete observation median window mean | 28.8039 ms | 8.2434 ms | 71.38% |

Both meet the unchanged70%-of-baseline thresholds. Benchmark used default
unpatched mode on the actual committed source, four environments, seed7,
zero residual actions, RGB+depth and10x20 six-family scene. Warmup50 steps;
5x100-step windows per metric. Capture99/hold400/reset1 observations and5 explicit
partial resets retained. Step windows 13.1896–13.6877ms;
observation windows 8.2153–8.3527ms.

Fresh executions:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
.venv/bin/python .scratch/issue_4/check_fused_prototype.py
.venv/bin/python -m compileall -q src tests
git show --format= --check HEAD
git diff --check
timeout --kill-after=10s 240s .venv/bin/python .scratch/issue_4/benchmark_performance.py --result .scratch/issue_4/performance-verify.json --device cuda:0 --viz none
```

Regression **169 passed** (35 upstream warnings); independent original-baseline
comparison **180 cases passed**. Compileall and whitespace checks passed.
Source SHA256 checks match performance-production-source-hashes.json. Termination
class matches baseline attempts class byte-for-byte; old file is absent. Prior
passed native sensor/RGB/reset and dynamics/curriculum checks are reused because
source is identical; they were not re-run in this Verify turn. Exact fresh logs:
performance-verify-pytest.log, performance-verify-equivalence.log,
performance-verify-benchmark.log. Raw benchmark and runner resource/exit evidence:
performance-verify.json, performance-verify-run.json.

RAM available before benchmark 18254440KiB, VRAM 7793MiB;
serial, headless,240-second bound. IsaacLab still346c74fe722ad371a6c663e3b384b3d172966d11.
No instability observed. Neither pyright nor mypy is installed; no static typecheck
was run. This limitation is unchanged and not a substitute claim of type safety.

| Acceptance | Evidence | Result |
|---|---|---|
| A1 snapshots/errors | fresh180-case baseline differential + sensor tests | Pass |
| A2 selectors and reset | public selector regressions; unchanged native partial-reset evidence | Pass |
| A3 regression/lazy termination | fresh169 tests, source/old-path check | Pass |
| A4 native sensor and dynamics lifecycle | source hashes match previously passed native runs | Pass, evidence reused |
| A5 committed production benchmark | fresh raw windows and runner exit0 | Pass |
| A6 separate30% reductions | table above | Pass |
| A7 reproducibility/limits | commands/logs/resources and unchanged limitations | Pass |

Verify is complete; user subsequently authorized remote delivery and closure of
completed performance sub-issues#17–#20, while retaining parent#4 open. Final
Verify evidence is included in a follow-up delivery commit. The
following implementation-stage results remain as historical evidence.

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
