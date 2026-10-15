# AGENTS.md

## Required workflow

For non-trivial changes:

1. Read REQUIREMENTS.md.
2. Read TEST_PLAN.md.
3. Establish baseline before changing behavior-sensitive code.
4. Perform impact analysis.
5. Implement the smallest necessary change.
6. Run existing tests and new tests.
7. Run regression and benchmark checks.
8. Record evidence in VERIFICATION.md.

## Test integrity

Do not weaken tests only to make implementation pass.

Changes to:
- acceptance thresholds
- expected outputs
- test fixtures
- test oracles

must be independently justified.

## Completion policy

Do not claim completion unless:
- applicable requirements pass;
- regression checks pass;
- verification evidence exists;
- remaining unverified items are reported explicitly.
