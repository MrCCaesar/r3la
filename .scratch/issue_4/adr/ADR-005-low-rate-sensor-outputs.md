# ADR-005 — Native low-rate sampling with stable exported samples

Status: Accepted for revised S14 and approved S15/S16 data semantics.
Approval reference: user yes to S15/S16, then yes to revised S14 after native-source investigation.

## Context / problem

Depth/body/four-foot target scans operate at 10 Hz. Native lazy scheduling and
reset invalidation already exist; current Newton renderer can write all camera
rows for a subset-triggered capture. Exported held samples need consistent ages
and must survive unrelated environments' resets.

## Alternatives

1. Equal periods and direct renderer buffer exposure: minimal changes, but ignores
   moving-camera pose and partial-reset output aliasing evidence.
2. Native scheduling plus explicit pose refresh and row-isolated held snapshots.
3. Independent project-wide scheduler: duplicates clock/reset logic and increases
   maintenance without removing the underlying renderer write-scope issue.

## Decision and rationale

Option 2. Keep native update_period/lazy reads and reset invalidation. Enable
update_latest_camera_pose. Export owned held samples updated only for environments
with a valid new capture; provide timing/validity metadata. Use approved metric
depth and scan conventions from interfaces.md. Adapter details remain to specify.

## Consequences / trade-offs

Additional output storage and copying, but no second scheduler. Must verify sample
identity, reset isolation and timestamps with two bounded environments after
approval to run. Do not infer that static investigation proves runtime behavior.
Base-yaw foot grids require a separately specified orientation adaptation.

## Evidence

research.md S14 follow-up, default SensorBase/Camera/BaseRayCaster lifecycle,
NewtonWarp render scope; requirements R22–R24 and S13 rate amendment.

## Final Specify consolidation reference

Current accepted contracts are in ../design.md and ../interfaces.md, consolidated
through S67. Earlier pending/open statements in this ADR describe its decision
history and are resolved by the subsequent numbered approvals. No runtime validation
is implied by Accepted status. Stage closure/Plan approval remains separate.

## Metadata removal amendment

Partially superseded by accepted ADR-010 after the user explicitly requested
removal of unnecessary metadata exports and consistency checks. Earlier evidence
and decisions above are historical; native lifecycle/held-buffer ownership remain.
