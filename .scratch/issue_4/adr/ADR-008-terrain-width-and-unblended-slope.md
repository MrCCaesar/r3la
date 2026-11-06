# ADR-008 — Equal-width narrow stairs and unblended transverse ramp

Status: Accepted. Approval reference: user correction on 2026-11-06 requesting
matching stair/platform Y widths for holes=True and a normal ramp rotated 90°,
without smooth joins to flat ground, with an attached paper illustration.

## Context and alternatives

Earlier S59–S64 geometry narrowed only the treads, leaving a wider residual
platform, and blended the transverse slope into flat ground over 0.5 m at each
X end. Keeping that geometry conflicts with the user's corrected intent.
Alternatives were retaining those blends/platform shoulders or applying the
requested uniform width and direct joins. The latter is selected.

## Decision and rationale

For stairs and tilted stairs with holes=True, every tread and the top platform
share Y span platform_width, centered on the same Y. Stair count and platform X
length retain their residual calculation. holes=False behavior is unchanged.
Support, completion inset and far gate are derived from the actual new platform.

The transverse ramp is one plane over x[3,5], y[4,6], with
z=(y-5)*tan(20*d degrees), mirrored as before. This is the surface of a longitudinal
planar ramp rotated 90° about Z. Remove both X transition ramps and close the
surface with vertical sides. Keep the prior centered height datum, footprint,
angle range, flat approach/landing and mirror convention; the user did not request
changes to these quantities. This supersedes the corresponding width/blending
clauses of design.md/interfaces.md and earlier ADR-001 geometry refinements.

## Consequences and evidence

Direct joins have discontinuous heights away from the centerline, intentionally.
The negative side must remain uncovered by the flat-ground slab. The top needs
only two triangles; no bilinear approximation grid is necessary. SideSlopeGeometry
break_x now has shape (2,) and contains [3,5]; this changes its data contract.
Geometry revision 2 participates in affected native cache keys and canonical
identity so old mesh caches cannot silently reappear. Other terrain family
identities retain their previous construction.

Tests cover both stair families' equal Y edges and outside-platform ray hits,
exact slope triangle interiors, direct joins, mirrors, watertight solids, derived
completion regions and cache reuse. Execution results are in verification.md.

## Accepted follow-up — ground-aligned low edge

Approval: user states the angle/join surfaces satisfy the requirement and requests
the minimum slope height to meet horizontal ground (2026-11-06). This supersedes
the centered-height datum above: canonical z=(y-4)*tan(20*d), mirrored
z=(6-y)*tan(20*d) over the same 2 m width. At d=0 the surface is flat. Angle,
footprint, direct joins, spawn/landing and staircase geometry are unchanged.
Only the solid base extends below ground; the traversable slope does not.
Geometry revision 3 prevents reuse of revision 2 centered meshes. Tests cover
low-edge height, full-plane nonnegative heights and exact mirrored surfaces.
