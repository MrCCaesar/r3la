# AGENTS.md

## Workspace Hygiene

1. Keep the repository clean while working.
2. Do not create log files solely to inspect command output if the output can be read directly from the terminal.
3. If command output must be redirected to a file for analysis, treat that file as temporary.
4. Store temporary diagnostic files outside the repository when practical.
5. Delete all temporary files created by the agent once they are no longer needed.
6. Before completing a task, review files created during the task and remove temporary diagnostic artifacts such as *.log, *.tmp, captured stdout/stderr, debug dumps, and intermediate inspection files.
7. Never delete files that existed before the task unless explicitly requested by the user.
8. Never delete experiment logs, training outputs, checkpoints, datasets, benchmark results, or other project artifacts merely because their filename matches a temporary-file pattern.
9. Files under `.scratch/` that belong to the configured issue tracker or active feature specifications are project workflow artifacts, not temporary diagnostic files, and must not be deleted by cleanup rules.

## Backend-Specific Imports

1. Do not import backend-specific modules at file scope in code shared by multiple physics backends.
2. Import backend-specific packages only inside the runtime branch or helper that actually uses that backend.
3. Backend selection must occur before backend-specific import.
4. Do not use `try/except ImportError` as a substitute for lazy imports.
5. For type hints only, use `TYPE_CHECKING`.

Example:

```python
if use_newton:
    from isaaclab.actuators.newton import read_group_parameter
```

Never:

```python
from isaaclab.actuators.newton import read_group_parameter
```

at module scope in shared code.

## Required workflow

For non-trivial changes:

1. Read the relevant feature spec and issue under `.scratch/`, if any.
4. Read relevant glossary entries and ADRs.
5. Establish a baseline before changing behavior-sensitive code.
6. Perform impact analysis.
7. Implement the smallest necessary change.
8. Run applicable tests and regression checks.
9. Record evidence in `VERIFICATION.md`.

Feature specs and issues may refine repository-wide requirements but must not silently contradict existing ADRs.

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

## Resource-Aware Testing

- Before running resource-intensive tests, inspect the host's available CPU, RAM, and GPU memory.
- Scale test parameters to the available resources; never assume the machine can run the maximum configuration in `TESTS.md`.
- Keep total test memory usage well below available memory and leave sufficient headroom for the OS and simulator.
- For IsaacLab tests, start with the smallest practical workload (for example, `num_envs=1` or `2`) and increase only when necessary.
- Prefer sequential or reduced-size tests over running multiple heavy tests concurrently.
- Do not run stress, large-scale, or high-parallelism tests unless explicitly requested.
- If estimated resource usage may exceed safe limits, reduce the test size instead of attempting the test.
- Resource limits override test-scale examples in `REQUIREMENTS.md` and `TESTS.md`; preserve test intent while reducing workload.
- For IsaacLab/Isaac Sim tests, default to num_envs <= 2 unless a larger value is required to validate the feature. Check available system RAM and GPU VRAM before increasing parallel environments, and stop scaling up when free memory becomes limited.

## Agent skills

### Issue tracker

Issues and specs use local Markdown under `.scratch/<feature>/`. Before reading or publishing tickets, read `docs/agents/issue-tracker.md`.

### Triage labels

Use the five default triage roles as issue status strings. Before triaging, read `docs/agents/triage-labels.md`.

### Domain docs

Use a single-context layout: root `GLOSSARY.md` and `docs/adr/`. Before exploring the codebase, read `docs/agents/domain.md`.
