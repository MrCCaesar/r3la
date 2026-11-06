# Metadata removal implementation checks

Completed under explicit user removal request. See ADR-010 and interface amendment.

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/test_parkour_sensors.py tests/test_parkour_evaluation.py -q`: 28 passed, 35 existing Torch JIT deprecation warnings.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`: 164 passed, same 35 warnings.
- Initial unfiltered pytest invocation failed before collection because an unrelated ROS plugin imports missing `lark`; disabled external plugin autoload using the repository's established invocation.
- Updated native sensor/evaluation/dynamics smoke scripts to inspect internal samples for diagnostic metadata and assert the reduced observation schema. These simulations were NOT run.
- No new runtime benchmark or full training run. Previous performance percentages refer to the previous implementation.
- GitHub Issue read failed with api.github.com connectivity error; existing local issue documents and latest user instruction supplied requirements.
- No commit, push or issue edit performed.

## Formal Verify — 2026-11-06

User explicitly requested “进入verify”. Scope is ADR-010's approved metadata
removal; full SWAP learner integration and new performance targets are outside
this check. Verification runs use the current uncommitted working tree.

Fresh static/regression checks:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
```

164 tests passed in 3.51 s; 35 upstream Torch JIT deprecation warnings.
Compilation and whitespace checks passed. Source scan found no remaining removed
metadata APIs in production code or active test scripts. A config/lazy-export
probe confirmed exactly proprio/commands/target/amp/privilege groups and absent
read_low_rate_targets/sensor_metadata exports. The probe ran without GPU access
and emitted Warp initialization and Matplotlib cache warnings; the GPU simulation
checks below ran outside that sandbox with CUDA available.

Native checks run serially with 2 environments, CUDA:0, no UI, and a 240 s timeout
each, using repository .venv/bin/python. RAM available before execution was
16–17 GiB; VRAM free was 7793 MiB. Sandboxed nvidia-smi could not access the driver;
outside-sandbox nvidia-smi and torch.cuda.is_available confirmed GPU availability.
No concurrent simulations or training launched.

```sh
timeout --kill-after=10s 240s .venv/bin/python tests/parkour_sensors_smoke.py --device cuda:0 --viz none
timeout --kill-after=10s 240s .venv/bin/python tests/parkour_evaluation_smoke.py --family box --level 0 --wrapper --device cuda:0 --viz none
timeout --kill-after=10s 240s .venv/bin/python tests/parkour_dynamics_smoke.py --device cuda:0 --viz none
```

Sensor check exited 0: known-plane depth/intrinsics, metric scans/base-yaw grids,
zero no-hit encoding, 10 Hz hold, 50 Hz critic, partial-reset identity and held-row
renderer isolation passed. Wrapper/evaluation check exited 0: exactly five output
groups, expected shapes/finiteness, deterministic reset, native TensorDict timeout
forwarding and auto-reset passed. The simulation observation dictionary and wrapper
output contain no metadata group. Logs: metadata-verify-pytest.log,
metadata-verify-sensors.log and metadata-verify-wrapper.log.

The existing MLP runner configuration's SWAP input incompatibility remains as
recorded in rsl-rl-training-data.md. Wrapper success does not demonstrate PPO
training, and this verification does not claim a new runtime speedup.

Dynamics check exited 0: applied dynamics/clean privilege and AMP, native terminal
step and pre-reset migration, fixed command/attempt bounds, and all-invalid height
reward fallback without reset passed (2 envs, 51 control steps).
Log: metadata-verify-dynamics.log. Native logs contain upstream deprecation and
Newton COM-query warnings, with no test failure or observed instability.

**Formal Verify result: PASS for ADR-010 metadata removal.** No production changes
were needed during Verify. No full training, performance benchmark, commit, push
or GitHub write performed. GitHub Issue read remains unavailable due to network
connectivity; the existing local Issue #4 documents were used.
