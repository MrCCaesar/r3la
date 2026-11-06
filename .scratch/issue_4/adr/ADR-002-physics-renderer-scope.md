# ADR-002 — Initial physics and renderer support scope

Status: Accepted. Approval reference: user approved S1/S2 with “1. yes” and “2. yes”, with the additions recorded below.

## Context / problem

Current configuration uses Newton MJWarp and Newton Warp rendering, with additional
physics presets. Source evidence shows backend differences in force/material and
invalid-depth semantics; preset presence is not validation.

## Alternatives

1. Validate current Newton MJWarp/Warp combination first.
2. Select a PhysX/renderer combination first, reconciling physical and sensor semantics.
3. Require multiple backends immediately, multiplying validation obligations.

## Decision and rationale

Option 1: one initial supported combination, retaining the existing intended
runtime while bounding validation work. Compatibility is a hypothesis to test,
not an asserted fact. Any necessary switch requires review of its impacts.

## Consequences / trade-offs

No multi-backend equivalence promise. Must verify dependency versions, material
writes, contact forces, actuators, cameras and reset data. Presets can remain in
existing code without being claimed as supported; removal is not proposed here.

## Evidence

research.md, “Backend and verification evidence”; current parkour_env_cfg.py.

## Deferred support

TODO-02: OVPhysX support and validation.
TODO-03: Isaac Sim PhysX (isaacsim_physx) support and validation.
User explicitly requested both as TODOs; neither is part of first implementation.
Compatible renderers, dependencies and physical/sensor parity need separate work.

## Final Specify consolidation reference

Current accepted contracts are in ../design.md and ../interfaces.md, consolidated
through S67. Earlier pending/open statements in this ADR describe its decision
history and are resolved by the subsequent numbered approvals. No runtime validation
is implied by Accepted status. Stage closure/Plan approval remains separate.
