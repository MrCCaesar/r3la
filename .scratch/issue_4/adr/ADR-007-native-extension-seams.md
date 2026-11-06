# ADR-007 — Native pipeline extensions for geometry, sensors and attempts

Status: Accepted (revised S35/P1). Approval reference: user “yes” immediately
following the revised S35 proposal.

## Context / problem

Accepted behavior requires actual sampled terrain difficulty and task regions,
stable per-row camera snapshots, base-yaw foot scans, and exactly-once pre-reset
attempt statistics. Native APIs expose most machinery but not these whole contracts.

## Alternatives

1. Unmodified primitives/direct sensor buffers/independent callbacks: insufficient
   metadata, output aliasing and duplicate/out-of-order metric risks.
2. Narrow project subclasses/accessors with one attempt-state owner, retaining
   native generator/importer, sensor clocks and environment step/reset order.
3. Replace environment loop/terrain pipeline or patch upstream IsaacLab: larger
   divergence, ownership and upgrade burden.

## Accepted decision and rationale

Option 2, as specified in interfaces.md P1. Terrain generator captures actual d
on both cache hits/misses; shared deterministic layout drives meshes and metadata.
Importer extracts final in-memory table via import_mesh. Camera copies legitimate
rows inside capture hook; scanner composes foot translation/base yaw. A single
termination-term state owner accumulates per-step outcomes and tracking, and one
native stateful curriculum term reads ending rows before native reset. A minimal
CommandTerm samples family-specific bounds using native reset/countdown with a
resampling period longer than the episode limit.

## Consequences / trade-offs

Several protected hooks/native timestamp fields are version-coupled. Confine them
inside adapters, pin source identity and test upgrades. Camera scalar override
loses native batch-camera eligibility; extra held storage/copies are deliberate.
No code edits to upstream IsaacLab and no custom RL environment loop are proposed.
No numeric geometry choice or learner behavior is approved by this ADR.

## Evidence

research.md Specify integration follow-up; local terrain_generator.py sampling/
cache/placement, terrain_importer.py import_mesh hook; Camera capture/batch hooks;
NewtonRaycastSensor pose mixin; ManagerBasedRLEnv pre-reset curriculum order;
manager_base.py separate construction of class terms. See interfaces.md contracts.

## S35 revision after native lifecycle review — Accepted

User requested reconsideration against installed IsaacLab. Earlier proposed
finalized-record/consumed-flag machinery is withdrawn: read ending rows directly in
the native pre-reset curriculum callback. No second episode scheduler or counter.
Native term reset clears attempt state; curriculum term reset preserves statistical
windows. Command constancy follows from native resampling period exceeding episode
length; custom sampler is justified only by per-family bounds and task metrics.
Terrain/sensor proposals unchanged. User explicitly approved the revised S35.

Evidence: manager_based_rl_env.py step/_reset_idx; curriculum_manager.py compute/reset;
command_manager.py reset/compute/_resample; velocity_command.py sampling and metrics.
Task score retains its own pre-reset accumulator to include the ending step without
coupling to private, weighted RewardManager episode sums.

## Final Specify consolidation reference

Current accepted contracts are in ../design.md and ../interfaces.md, consolidated
through S67. Earlier pending/open statements in this ADR describe its decision
history and are resolved by the subsequent numbered approvals. No runtime validation
is implied by Accepted status. Stage closure/Plan approval remains separate.
