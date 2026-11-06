# ADR-003 — Ordered traversal and finite landing confirmation

Status: Accepted (structure only).
Approval reference: user “3. yes 4. yes” accepting Specify S3 and S4.

## Context / problem

Success must mean passing the assigned obstacle with necessary landing, reject
bypass, and balance physical validity against implementation complexity (R10,
R12–R19). Crossing a position threshold while airborne is insufficient.

## Alternatives

1. Far-side position only: cheap but violates the approved landing requirement.
2. Position plus one contact instant: can accept edge brushing and failed landings.
3. Ordered legal traversal plus finite landing confirmation: modest task state,
   observable position/contact/motion evidence; finite approximation.
4. Extended post-obstacle motion or stability estimation: greater complexity and
   additional assumptions, without a guarantee against all future falls.

## Decision and rationale

Option 3. Task routes follow S3 in design.md: box-top completion, staircase-top
platform, far-side gap landing, and exit regions after slopes/rock patches.
Require legal traversal, base entering the completion region and a short landing
confirmation with support, acceptable attitude/vertical motion and no failure.
Do not require all four feet to contact simultaneously. Failure from base
collision, bypass or timeout overrides coincident completion. Success ends the
attempt and triggers reset as already required.

## Consequences / trade-offs

Finite confirmation cannot guarantee no later fall. Numeric thresholds, contact
aggregation, confirmation duration and geometric margins remain unapproved.
The method must tolerate legitimate gait and terrain tilt; it must not silently
turn all terrain types into flat-ground standing tasks. Later tests must include
failed landings, bypass, permitted leg collisions and simultaneous outcome events.

## Evidence

requirements.md R10/R12–R19; research.md terrain/success alternatives and manager
ordering; explicit S3/S4 approval in this conversation.

## S23 numeric confirmation approved

Approval reference: user “23. 基座姿态，roll,pitch小于30度。其他yes”.
Accepted 0.2 s window, strict absolute roll/pitch <30 degrees, absolute world
vertical speed <=0.5 m/s, support >1 N world-up normal component in >=half the
control samples, >=two distinct supporting feet in the window, support at the
final sample, continuous region/pose/speed validity and failure precedence.
Details and restart behavior are authoritative in design.md S23 plus its amendment.
These are configurable initial values; no runtime classification accuracy claimed.

## Accepted support attribution refinement — S52

Context: upward foot force alone cannot identify the target landing surface.
Alternatives: force alone; foot-center approximation; native filtered contact
positions plus target geometry. Choose the third: finite native terrain contact
point within full landing XY bounds and <=0.03 m perpendicular plane distance,
together with approved upward normal force >1 N. Base still uses inset region.
Rationale: uses actual contact locations with bounded geometric tolerance.
Trade-off: native points are force-weighted aggregates; mixed/edge contacts require
verification, not a claim of exact mesh-face attribution. Missing points do not
count; unsupported tracking fails setup, no extra runtime reset condition.
Evidence: research.md contact-position source follow-up. Approval reference: user
“yes” in response to S52. Existing confirmation window remains authoritative.

## Final Specify consolidation reference

Current accepted contracts are in ../design.md and ../interfaces.md, consolidated
through S67. Earlier pending/open statements in this ADR describe its decision
history and are resolved by the subsequent numbered approvals. No runtime validation
is implied by Accepted status. Stage closure/Plan approval remains separate.
