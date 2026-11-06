# Issue #4 — Performance implementation plan

Status: **Approved** — user “yes” approved T13–T16 breakdown and publication.
User explicitly approved the detailed specification and invoked to-tickets to
enter Plan (2026-11-06). The configured tracker is GitHub MrCCaesar/r3la;
publication uses ready-for-agent and parent#4. All four tickets have been published; read-back validation passed for labels,
parent#4 and exact native blocking relationships.
Production implementation is now complete for T13–T15 under the subsequent user implement instruction.

## Confirmed scope

Approved performance-spec.md PS1–PS5 and ADR-009 are authoritative. Four-env
observation and full-step time must each drop at least30%; preserve functionality,
no cross-call cache, retain RGB/depth and full scene. Move the sole termination
state implementation, remove old direct import, keep public lazy export.

## Proposed independently verifiable tickets

| Ticket | Complete delivery | Blocked by | Contract trace |
|---|---|---|---|
| T13 | Fast validated public low-rate bundle, same values/errors/lifecycle, unit/differential and bounded sensor evidence | None | PS1, PS3; A1, A4 |
| T14 | Full observation-manager selectors return only requested fields, same validation/ownership/reset behavior | T13 | PS2, PS3; A2, A4 |
| T15 | Single termination owner in native-convention module, migrated imports/lazy export and working curriculum | None | PS4; A3, A4 |
| T16 | Final integrated regression and reproducible >=30% observation AND full-step performance acceptance | T14, T15 | PS5; A1–A7 |

T13 precedes T14 because the selector path consumes its validated sample reader.
T15 has no data or implementation dependency on T13/T14 and may be picked from
the frontier independently. T16's T13 dependency is transitive through T14, so no
redundant direct edge is needed. Recommended serial working order T13,T14,T15,T16;
this preference does not create an artificial blocking relationship. All native
simulations remain serial regardless of independent code tasks.

T13 includes the small prefactor and its first working caller rather than a
horizontal helper-only ticket. T15 moves one class plus its consumers atomically;
its blast radius is small, so no expand-contract compatibility layer is needed
(and user explicitly rejected keeping the old path).

Each ticket carries its own tests/documentation: T16 integrates evidence and
acceptance, not deferred testing for otherwise incomplete earlier slices.

## Draft ticket bodies

One reviewable issue draft per ticket: performance-tickets/T13.md through T16.md.
These are publication drafts, not a replacement local tracker. They deliberately
avoid filesystem paths; interface names and contract semantics identify scope.

After breakdown approval: check duplicates, publish in dependency order, label
ready-for-agent, attach to parent#4 using native sub-issue relationships, and set
native blocking edges where available. Preserve a ticket-ID/URL mapping and
verify the resulting relationships. Do not edit parent title/body/comments or
close the parent. If native blocking is unavailable, list real blockers in ticket
bodies and record that limitation.

## Execution and stage boundaries

Publication under the explicitly invoked skill does not authorize production
implementation by itself. Implement starts only after user approval. T13–T15
include necessary implementation checks; T16 formal integrated Verify follows
stage authorization. Do not commit/push or close issues without a new instruction.

## Open questions / recommendation

Are four slices appropriately sized; do edges T13→T14→T16 and T15→T16 match the
user's expectations; should any be merged/split? Recommend approving this split.
No new architecture decisions or requirements are introduced by this plan.

## Checks

Read parent issue title/body/comments and tracker/triage instructions; inspected
approved specification and current call sites. Planning changes only: no new
runtime test run, because no production code changed. Research evidence remains
in performance-research.md; it is not final implementation acceptance.

## Publication mapping

- T13: https://github.com/MrCCaesar/r3la/issues/17
- T14: https://github.com/MrCCaesar/r3la/issues/18
- T15: https://github.com/MrCCaesar/r3la/issues/19
- T16: https://github.com/MrCCaesar/r3la/issues/20

Publication verification: performance-publication-verification.json. Initial
read-back encountered a network failure; a read-only retry verified all four
issues successfully. No duplicate creation was needed. Native relationship API
references: https://docs.github.com/en/rest/issues/issue-dependencies and
https://docs.github.com/en/rest/issues/sub-issues. Parent content/state was not
edited; only the explicitly requested child relationships were added.

Plan stage complete; user subsequently authorized Implement via the implement skill. T13–T16 execution/results are recorded in performance-verification.md.


## Implementation completion

T13–T16 completed under user implement authorization. All functional and
performance evidence, two-axis review fixes and limitations are recorded in
performance-verification.md. GitHub task status is unchanged; no closure requested.


Formal Verify completed on user instruction “进入verify”; all A1–A7 criteria passed
on committed implementation cbd6423. Latest evidence: performance-verification.md.
