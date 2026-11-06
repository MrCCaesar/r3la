# Issue #4 — Performance follow-up requirements

Status: Explore/Research complete; no-cache direction and Specify entry approved. User invoked grill-with-docs on 2026-11-06.

## Confirmed intent

- Baseline current environment observation calculation and step runtime.
- Optimize without changing functionality; target at least 30% improvement.
- Investigate repeated full read_low_rate_targets calls from observation terms.
- Put ParkourAttemptState with termination terms in terminations.py and align
  comparable module organization with installed IsaacLab conventions.
- Use repository .venv Python; bounded serial headless simulations, **4 envs** explicitly selected by user.

## Confirmed initial facts

Starting commit: 5768061. sensor_observations.py low_rate_target and most
sensor_metadata calls each invoke read_low_rate_targets, which reads six sensors,
validates shapes/metadata and performs GPU tensor comparisons. The cost and
proportion of full step time have not been measured. Repeated reads do not by
themselves prove repeated physical captures, since native lazy scheduling applies.

## Round 1 — confirmed by user

Approval: “1. yes 2. 4个环境 3. yes 4. yes”.

1. Both observation calculation and complete env.step median timings must be
   <=70% of their respective baseline, not merely 30% throughput improvement.
2. Four environments; same configuration/actions/seed before and after.
3. Predefined numerical tolerance for floats; preserve masks, shapes, clocks,
   reset/history/randomization and discrete decisions. No reduced sensor
   rates/resolutions or removed effective checks as a hidden optimization.
4. Limit readability changes to task MDP ownership and related imports;
   preserve public mdp exports and native lazy imports.

## Further confirmed facts

- Full observation computation calls the bundle reader 16 times: six target
  terms and ten metadata terms, resulting in 96 read_sample calls, 80 tensor
  equality checks and 160 allclose checks. These counts are static evidence,
  not runtime profiling or proof of repeated captures.
- Current task front_camera explicitly requests rgb + distance_to_image_plane;
  the depth-only default in HeldDepthCameraCfg is overridden by the task.
- Reset may occur without a changed common_step_counter. Native observation
  initialization also probes terms. A step-counter-only cache is not sufficient
  evidence of correct invalidation.
- Native task examples place stateful termination terms in terminations.py and
  expose them through lazy mdp exports. Existing test code directly imports
  mdp.attempts, while task configuration uses mdp.ParkourAttemptState.

## Round 2 frontier — proposed, not yet approved

5. Baseline retains current RGB+depth, all sensor rates, physics and six terrain
   families. Use synchronized complete timing windows containing multiple 10 Hz
   capture cycles, report median per-window average plus capture/hold/reset
   breakdown; do not select only warmed sensor reads or cheap individual steps.
   Observation timing covers the actual full manager calculation during step;
   full-step timing is measured separately without intrusive inner synchronization.
6. User decision: move implementation and all project imports to terminations.py;
   retain public mdp.ParkourAttemptState, remove mdp.attempts without a compatibility
   shim. Do not create duplicate state ownership.
7. Approve Explore closure and Research entry for resource-checked, bounded 4-env
   baseline/profiling experiments. Do not optimize production code until design
   and implementation plan are confirmed. No guarantee of meeting 30% absent data.

## Deferred decisions

Measurement protocol/sample count, CUDA synchronization, profiling experiments,
cache ownership/invalidation, validation strategy, ADR and implementation plan
follow settled requirements and measured evidence. No production edit or benchmark
run performed in this interview round. No speedup is claimed or guaranteed.

## Round 2 approval

User: “5. yes”, explicit no-old-import decision for 6, “7. yes”. Measurement
boundary accepted; Explore closed and Research baseline/profiling authorized.
Production optimization remains pending design/plan approval.

## Research outcome / next frontier

Scratch fused-check prototype measured step -60.08%, observations -70.01% on
the approved four-env workload. See performance-research.md for exact evidence
and limits. Proposed next decision: choose no-cache fused validation plus
on-demand selectors, then authorize Specify. No production optimization yet.

## Q8 approval

User “yes” approved no-cross-call-cache fused validation with on-demand selectors
and Specify entry. Detailed proposed contract: performance-spec.md. Implementation
and final performance acceptance remain pending.
