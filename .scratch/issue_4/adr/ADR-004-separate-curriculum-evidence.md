# ADR-004 — Separate evidence for terrain and velocity curricula

Status: Accepted, including subsequently approved S7/S8 and S21 bounds.
Approval reference: user “5. 同意，但是修改达到最高等级后随机退回低等级 6. yes”.

## Context / problem

R11 requires terrain progression from successful passage and velocity progression
from tracking quality. Early completion makes fixed-maximum-duration log averages
misleading; stock distance curriculum is not success-rate evaluation.

## Alternatives

- Reuse distance curriculum and public reset metrics: conflicts with the approved
  semantics and lifecycle evidence.
- Per-attempt binary terrain progression or EMA: simpler/no fixed sample window,
  but different noise/interpretability trade-offs.
- Rolling per-family/level success rate and actual-attempt velocity score: explicit
  statistical meaning with additional state.

## Decision and rationale

Use per-family/level last-100-attempt terrain success rates; require 20 samples;
promote at >=0.8, demote at <=0.3, otherwise hold. Ordinary changes are one level.
User explicitly requested random return to lower difficulty at the highest level,
superseding the proposed saturation rule; exact recycling semantics are pending S7.

Use actual-attempt average q=(r_linear+0.5*r_yaw)/1.5 for velocity quality, including
zero-target lateral/yaw tracking and excluding other rewards. The two curricula
have distinct evidence; passage success is not silently required for speed growth.

## Consequences / trade-offs

Window/thresholds are configurable project choices, not paper-provided constants.
Statistics need consistent attempt identity and pre-reset finalization. Short
attempts and old samples need explicit handling. S8 velocity aggregation and update
parameters remain unapproved. No convergence or runtime verification is claimed.

## Evidence

requirements.md R11/R20; research.md manager/metric timing and curriculum alternatives;
design.md S5/S6 and user amendment.

## S7/S8 approval extension

Approval reference: user “7. yes 8. yes”. Previously pending S7/S8 are now Accepted.
At highest-level promotion, uniformly choose a lower level (single-level case
holds). Speed curriculum uses separate family upper bounds and batches of 20
attempts lasting >=1 s, equal attempt weights, +/-0.1 m/s at mean q >=0.8 / <=0.3,
then clears the batch. Fixed commands per attempt; new ranges apply next attempt.
Initial/max speed bounds remain open. Detailed contract is in design.md S7/S8.

## Final Specify consolidation reference

Current accepted contracts are in ../design.md and ../interfaces.md, consolidated
through S67. Earlier pending/open statements in this ADR describe its decision
history and are resolved by the subsequent numbered approvals. No runtime validation
is implied by Accepted status. Stage closure/Plan approval remains separate.
