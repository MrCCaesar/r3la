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

1. Read REQUIREMENTS.md.
2. Read TESTS.md.
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
