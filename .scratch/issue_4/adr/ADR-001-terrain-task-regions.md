# ADR-001 — Terrain generation and explicit task regions

Status: Accepted. Approval reference: user approved S1/S2 with “1. yes” and “2. yes”, with the additions recorded below.

## Context / problem

Stock origins may be on box tops/stair summits. Stock ring/pyramid geometry does
not automatically express an intended traversal. R9/R12/R15/R19 require consistent
obstacle attempts with bypass rejection, while official APIs should be reused.

## Alternatives

1. Unmodified primitives and origin-based completion: little code, but origin and
   distance alone do not meet traversal/landing semantics.
2. Official pipeline, selective primitive reuse/custom terrain functions and
   explicit task regions: extra metadata and geometry validation.
3. Replace the entire terrain pipeline: maximum control, larger maintenance burden.

## Decision and rationale

Choose option 2. Use task-local +X as forward; distinguish entry/spawn, legal
traversal and landing/completion regions. Reuse matching primitive geometry;
provide missing directed/tilted/rock geometry through project terrain functions.

## Consequences / trade-offs

Task-region metadata must follow terrain placement, difficulty, mirroring and
cache identity. Exact per-family geometry and metadata contract remain undecided.
A box-top landing can be the completion region; climbing down is not implied.
Finite landing validation will be specified separately.

## Evidence

research.md, “Terrain, success and curricula”, especially origin semantics and
primitive comparison; approved requirements R9–R19.

## Approved convention

Custom sub-terrain functions/configuration classes follow
/home/sevnce-mr/IsaacLab/source/isaaclab/isaaclab/terrains and reside under
src/r3la/labs/terrains. Keep generation functions and configuration definitions
organized according to the corresponding official mesh/heightfield conventions.
Exact new filenames and public names remain to be specified.

## Approved geometry refinements

S29/S30: user changed box/stair top to 1.5x1.5 m and accepted 0.15 m completion
inset. User restricted tilted/mirrored terrain variants to slopes and stairs;
this supersedes the prior broader tilted-family scope. Other standard families
remain in scope. Exact mesh construction must preserve these approved semantics.

## Accepted random-grid adaptation (S43/S44)

Context: native random_grid_terrain samples signed heights, always inserts a center
platform and rejects zero residual border. These conflict with approved exact
2 x 2 m / 0.20 m positive-height patch geometry.
Alternatives: change approved geometry to native defaults; wrap and mutate native
meshes; adapt its box-grid construction locally. Choose local adaptation, preserving
exact tiling, U[0,h(d)] heights, no center platform and shared layout metadata.
Trade-off: project maintains a small terrain function and seed/cache checks;
avoids fragile mesh postprocessing or upstream edits. Evidence: research.md S43
source comparison. Approval: user “43.yes” for geometry and “44. yes” for adaptation.

## Accepted stair-count amendment — S59

User supersedes fixed-four-step geometry: count derives from obstacle dimensions
and tread depth; highest stair tread is separate from the top platform. Retain
approved tread depth, rise range, holes behavior and platform dimensions. Unlike
fixed count, configurable region size now affects total ascent and mesh bounds;
validate those dependencies. Formula/remainder and platform-relative height remain
open, not silently accepted. Approval reference: explicit user S59 correction.

## Accepted native residual stair platform — S60–S62

Context: native count formula and exact physical1.5 m platform conflict for general
region sizes. Alternatives: adapt count to force exact platform; accept native
residual platform. User chose native residual rule. Keep platform_width=1.5 as
parameter; derive physical platform and native additional platform rise. Completion
uses actual platform inset0.15 m on every side, per user's immediate correction;
center-only proposal is superseded. Consequence: stair completion/width metadata
must derive from actual geometry, not old fixed1.2 m region. Box dimensions stay.
Evidence: research.md S60/S61 source check. Approval: explicit user native-rule
selection followed by corrected actual-boundary inset instruction. Region/border
and tilt transform defaults remain open, not inferred approvals.

## Accepted entrance-excluded count region — S63/S64

Count uses post-entrance remaining region rather than full tile. With approved
entrance x3 and tile10x10, user accepted size7x10,border0. Native min-axis formula
produces10 treads and1x4 m residual platform, with one further rise to platform.
Keep +X flight at x3; full native four-sided placement is not adopted. Consequence:
platform completion inset0.7x3.7 m is additionally constrained by existing2 m
legal corridor. No silent squaring or widening. Approval: explicit S63 correction
followed by “yes” to S64's numbers. Tilt transform remains unresolved.

## Accepted tilted-tread-only geometry — S65

Context: tilt must be applied to defined surfaces. Proposed all-surface shear and
approach transition were amended by user: retain sheared treads but horizontal
entrance/platform. Decision: tread k uses k*h+(y-5)*tan(theta); approach0, platform
(N+1)*h. XY/count unchanged. Alternatives (whole-obstacle rotation or approach/
platform shear) are not selected. Consequence: first and last boundary rises vary
laterally and can become downsteps; preserve geometry and validate joins rather
than silently changing angle/height or filling low-side treads with flat ground.
Evidence: analytical surface equations. Approval: explicit S65 user correction.

## Final Specify consolidation reference

Current accepted contracts are in ../design.md and ../interfaces.md, consolidated
through S67. Earlier pending/open statements in this ADR describe its decision
history and are resolved by the subsequent numbered approvals. No runtime validation
is implied by Accepted status. Stage closure/Plan approval remains separate.
