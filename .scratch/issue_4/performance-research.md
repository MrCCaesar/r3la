# Issue #4 — Performance research

Status: Research completed; no-cache design direction approved by user Q8 yes.
Detailed Specify contract is proposed in performance-spec.md.
Date: 2026-11-06. Baseline commit: 5768061d5ee4cdf4fb33dbe31d5093476ef601a0.
IsaacLab: 346c74fe722ad371a6c663e3b384b3d172966d11.

## Confirmed experimental setup

User authorized 4 environments and complete current workload. RTX 4060 Laptop
GPU (8188 MiB), Torch 2.11.0+cu130, native Newton MJWarp/Warp renderer. Current
10x20 terrain grid and all six configured families retained, RGB + image-plane
depth retained, seed7, zero residual action, no learner, headless. 50 warmup steps,
5 timing windows of 100 steps for each metric, then 30 diagnostic steps and five
explicit one-row resets. Each process has a 240-second external timeout and runs
serially. Before baseline: available RAM17533 MiB / free VRAM7793 MiB; before
prototype: RAM16954 MiB / VRAM7793 MiB. No resource instability observed.

Full-step timing synchronizes CUDA only at window boundaries. Observation timing
wraps the actual native manager.compute inside real steps with CUDA sync at both
boundaries, in a separate phase so interior instrumentation does not contaminate
full-step timing. The acceptance statistic is median of five per-window means.
Capture/hold/reset categories are sampled outside the timed observation call.
Setup/JIT time is excluded. GPU diagnostics and observation timing are NOT added
together or treated as an exact decomposition of the independently timed step.

## Measurements (milliseconds)

| Metric | Baseline | Fused-check prototype | Reduction |
|---|---:|---:|---:|
| Full step, median window mean | 34.3336 | 13.7055 | 60.08% |
| Observation, median window mean | 28.8039 | 8.6396 | 70.01% |
| Capture observation mean (99 samples) | 28.9650 | 8.7789 | diagnostic |
| Held observation mean (400 samples) | 28.7273 | 8.6210 | diagnostic |
| Reset observation (1 sample) | 30.1227 | 10.4148 | insufficient sample for generalization |
| Explicit partial reset median (5 samples) | 33.3919 | 12.7354 | diagnostic |

Baseline full-step windows range34.2798–34.5677; prototype13.6085–13.7550.
Baseline observation windows range28.6652–28.8307; prototype8.6192–8.7272.
Measured bundle calls/observation remain16 in both. Diagnostic accumulated bundle
wall time is92.64% of observation time in baseline,78.06% in prototype. These
shares are instrumented diagnostic evidence, not independent speedup proof.

## Mechanism and prototype limits

Current 16 term calls read six samples each. Each bundle performs five torch.equal
and ten torch.allclose checks and dynamic boolean indexing. Host-visible decisions
serialize CPU/GPU work. Native lazy sampling avoids duplicate physical captures,
but does not remove these repeated validations and tensor allocations.

Scratch-only prototype stacks metadata and evaluates fixed-shape boolean checks,
with one host decision for the success case. On failure it invokes the original
validator to preserve exact error priority/type/message. Shape/dtype/device checks,
NaN and infinity behavior, tolerance1e-6, both-captured masks and uncaptured rows
are preserved. No persistent cache, new scheduler, environment subclass or upstream
patch is introduced. Production files remain unchanged.

Existing sensor test module under prototype injection:16 passed. Standalone
check_fused_prototype.py:120 CPU cases match output values/masks/metadata and exact
exception types/messages, including tolerance, uncaptured rows, NaN/Inf and
combined errors. These checks do not replace full eventual production verification
or the prior native sensor/reset isolation tests.

## Alternatives and recommendation (Proposed)

A. Fuse validation and separate validated sample access from complete bundle
assembly. Each configured selector returns only its requested value/metadata;
the public read_low_rate_targets still assembles the complete documented bundle.
No cross-call cache. Prototype proves fused validation alone exceeds the target
for the approved workload. Recommend this first, given the smaller lifecycle risk.
It intentionally does not promise to reduce16 validations to1.

B. Shared cache with explicit lifecycle revisions. Could further deduplicate,
but must invalidate on sensor.update (age), capture, partial reset, initialization,
sensor replacement and same-step reset. A step-counter-only cache is invalid;
borrowed metadata can also be externally mutated. This requires new ownership
and mutation contracts for selectors; not approved and not prototyped.

C. Compute-scoped manager cache. Native load_managers hardcodes ObservationManager;
there is no config class seam. Environment/manager integration would broaden the
architecture and create compute_group/construction/reset considerations. Not
recommended for an already-attainable performance target.

Readability: move sole ParkourAttemptState implementation from attempts.py to
terminations.py and migrate tests/import stub. Retain mdp.ParkourAttemptState via
native lazy export; remove attempts.py as explicitly requested. This file move
has no claimed runtime speedup. Other term ownership changes require concrete
misplacement evidence, not a blanket module merge.

## Primary local evidence

- src/r3la/tasks/velocity/mdp/sensor_observations.py: bundle and selector reads.
- src/r3la/tasks/velocity/config/Unitree/parkour_env_cfg.py: six target terms,
  ten bundle metadata terms; full current sensor/render configuration.
- src/r3la/labs/sensors/sample.py: capture/reset mutation and freshly computed age.
- IsaacLab source/isaaclab/isaaclab/managers/observation_manager.py: per-term
  evaluation, constructor probing, reset, cloned borrowed output ownership.
- IsaacLab source/isaaclab/isaaclab/envs/manager_based_env.py: hardcoded manager.
- IsaacLab source/isaaclab/isaaclab/envs/manager_based_rl_env.py: native step order.
- IsaacLab source/isaaclab_tasks/isaaclab_tasks/core/lift/mdp/terminations.py:
  stateful termination term convention (see installed tree for exact package path).

## Reproduction and artifacts

All commands executed from repository root with .venv/bin/python:

```sh
timeout --kill-after=10s 240s .venv/bin/python .scratch/issue_4/benchmark_performance.py --result .scratch/issue_4/performance-baseline.json --device cuda:0 --viz none
timeout --kill-after=10s 240s .venv/bin/python .scratch/issue_4/benchmark_performance.py --variant fused --result .scratch/issue_4/performance-fused.json --device cuda:0 --viz none
.venv/bin/python .scratch/issue_4/check_fused_prototype.py
```

Logs: performance-baseline.log, performance-fused.log,
performance-fused-equivalence.log. Full raw timing windows in respective JSONs.
The prototype is performance_fused_prototype.py; harness imports it only with
--variant fused. A baseline subprocess never monkey-patches production functions.

## Limits and open decision

Four environments occupy terrain columns[0,4,9,14] (box,gap,stairs,side_slope).
All six terrain families remain in the scene; this is not robot traversal coverage
of all six families or training-scale throughput. Zero actions are a reproducible
micro-workload, not a trained policy. Only one natural reset occurs in the timed
observation phase; reset is separately exercised. Performance for thousands of
environments is not inferred. Torch peak allocation excludes native/Warp memory.

Research recommendation awaits user choice of A versus deeper cache work, and
approval to enter Specify. Production implementation, full equivalence verification
and final >=30% acceptance have not yet happened.
