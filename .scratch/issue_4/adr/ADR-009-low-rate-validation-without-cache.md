# ADR-009 — Reduce low-rate validation synchronization without cross-call caching

Status: Accepted; detailed performance specification also explicitly approved
by user when entering Plan on 2026-11-06. Approval reference: user “yes” to Q8 selecting fused validation,
on-demand selectors, no persistent cache and termination relocation, 2026-11-06.

## Context

Issue#4 performance follow-up requires observation and full-step runtime reductions
of at least30% each with4 environments, without changing functional behavior.
Sixteen observation terms each assemble/validate a six-sensor bundle. Native lazy
sampling prevents repeated captures but does not remove costly host-visible GPU
checks. Baseline measured34.3336ms full step and28.8039ms observations.

## Alternatives

1. Fuse the checks and return only requested fields, retaining fresh reads.
2. Shared cache invalidated by explicit sensor lifecycle revisions.
3. Custom compute-scoped manager cache/environment integration.

## Decision and rationale

Choose1. A scratch fused-check prototype already reduced full step60.08% and
observations70.01% on the approved workload. Fresh validation preserves direct
read/reset/mutation behavior and avoids new cache ownership. A step-counter cache
cannot distinguish same-step partial resets; native clock advance also affects
sample age without a fresh capture. The native manager has no configuration seam
for replacing its class without broader environment integration.

## Consequences and trade-offs

Sixteen validations and96 low-rate sample reads may remain; we deliberately avoid
an implicit first-term barrier or lifecycle cache. Successful alignment validation
uses a combined GPU decision; a failure diagnostic preserves per-sensor precedence
on the same snapshots. Full bundle construction remains available only through
its existing public API. Native timing, owned sensor samples and manager cloning
remain intact. More synchronization reduction is possible but is not needed to
justify new cache state before final production measurements.

## Evidence and limits

performance-research.md, performance-baseline.json and performance-fused.json;
16 existing sensor tests and120 prototype differential cases. These are research
results, not final implementation acceptance. Related ADR-005 and ADR-007 retain
their scheduling/sample ownership/environment lifecycle decisions.
