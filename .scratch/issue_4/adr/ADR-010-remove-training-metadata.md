# ADR-010 — Remove training metadata export and observation consistency checks

Status: Accepted. Approval reference: user “取出不必要的metadata导出和一致性检查”,
following installed PPO investigation and confirmed reconstruction semantics.

## Context and evidence

Standard installed RSL-RL PPO does not consume sensor identity/time/validity
metadata. Reconstruction intentionally includes delivered sensor errors.
See rsl-rl-training-data.md and metadata-training-discussion.md. Cross-sensor
checks require unrelated reads and GPU-to-host decisions on every target access.

## Alternatives

1. Retain exported metadata and fused consistency checks (prior ADR-009).
2. Remove exports but retain all-six-sensor checks for every target.
3. Remove exports and checks; read only the selected sensor (selected).

## Decision and rationale

Remove MetadataCfg and the metadata observation group. Remove sensor_metadata,
LowRateTargets/read_low_rate_targets and the six-sensor validation layer.
low_rate_target(env, key) reads only that sensor's sample values. No cross-call
cache, rescheduling or masking is added. Internal sample fields, owned camera
buffers, native invalidation and metric validity processing remain necessary
for sensor behavior, diagnostics and height rewards; AMP validity is unchanged.

## Consequences and compatibility

The public observation dictionary loses metadata; direct users of the removed
bundle/metadata APIs must migrate. Diagnostic tests read sensor samples directly.
Cross-sensor mismatches no longer raise from observation reads. Native sensor
errors still propagate. Targets preserve dtype, shape, device and value encoding.
This supersedes ADR-009's validation/bundle decisions and ADR-005's requirement
to export timing/validity as training observations, not their native lifecycle
and buffer ownership decisions. No new performance percentage is claimed.
