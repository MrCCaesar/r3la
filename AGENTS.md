# AGENTS.md

## Workflow

For every non-trivial change:

1. Read the relevant GitHub Issue.
2. Read:
   - `.scratch/issue_<id>/REQUIREMENTS.md`
   - `.scratch/issue_<id>/TEST_PLAN.md`
3. Establish a baseline before changing behavior-sensitive code.
4. Perform impact analysis and classify affected code as:
   - `MUST CHANGE`
   - `MAY CHANGE`
   - `MUST NOT CHANGE`
5. Implement the smallest change required.
6. Run applicable tests, regression checks, benchmarks, and review `git diff`.
7. Record results and evidence in:
   - `.scratch/issue_<id>/VERIFICATION.md`

## Change rules

Do not:

- make unrelated changes;
- refactor or rename unrelated code;
- change existing behavior unless required;
- weaken tests or acceptance criteria to make code pass.

Preserve existing APIs and behavior unless explicitly required otherwise.

## Test integrity

Tests must verify the implementation independently.

Changes to acceptance thresholds, expected outputs, fixtures, oracles, or negative controls require explicit justification.

## Verification

Where applicable, verify:

- build;
- existing tests;
- new feature tests;
- regression tests;
- differential behavior;
- performance;
- final `git diff`.

For robotics, MPC, numerical, or real-time code, also check applicable numerical error, latency, jitter, memory allocation, deadline violations, and constraint violations.

## Completion

Do not claim completion unless:

- applicable requirements are satisfied;
- required verification passes;
- evidence is recorded;
- unrelated changes are absent;
- unverified items and remaining risks are reported.

Passing tests alone is not sufficient.

## Independent review

For non-trivial changes, use a separate review task when practical.

The reviewer must not modify the implementation.

Final result:

- `PASS`
- `FAIL`
- `PARTIALLY VERIFIED`

Every result must include evidence.