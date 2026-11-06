# ADR-006 — Go2 height reference and numerical contact semantics

Status: Accepted. Approval reference: user “19 yes 20. yes”.

## Context / problem

World-z height penalties depend on terrain elevation. Idealized nonzero force
contacts do not specify finite simulation thresholds or substep aggregation.
Requirements demand explicit Go2 adaptations and only base collision as illegal.

## Alternatives

- Absolute world height; local mean terrain height; richer supporting-surface estimator.
- Exact >0 force vs numerical >1 N; current sample only vs full control interval;
  normal vs total contact force.

## Decision and rationale

Use base world z minus mean valid critic-scan terrain z for height penalty and
stance reward; nominal target 0.4 m. This follows the existing scanner approach
with a consistent reference. Invalid-ray fallback is not selected here.

Use >1 N normal-force contact detection. Base illegal contacts and thigh/calf
collision penalties cover all four physics steps per control step. Critic flags
use the latest sample. Preserve separate total-force stumble ratio semantics.

## Consequences / trade-offs

Mean terrain blends surfaces at edges. Nominal height is authored/configured,
not a validated standing measurement. Force threshold/history are acknowledged
adaptations, not exact equivalence to the paper's idealized contact formula.
Need verify first-step history/reset behavior and ensure each link counts once.

## Evidence

research.md reward findings; local envs/mdp/rewards.py and terminations.py;
approved S19/S20 and requirements R3/R6/R14.

## Invalid-height policy approved (S26)

User “25. yes 26. yes” accepted zero height-related reward contributions when no
critic scan hit is valid, with explicit invalidity reporting. Neither ground-z-zero
nor stale-height substitution is used. This removes height shaping temporarily;
verification must inspect invalidity frequency. No new reset condition is introduced.

## Final Specify consolidation reference

Current accepted contracts are in ../design.md and ../interfaces.md, consolidated
through S67. Earlier pending/open statements in this ADR describe its decision
history and are resolved by the subsequent numbered approvals. No runtime validation
is implied by Accepted status. Stage closure/Plan approval remains separate.
