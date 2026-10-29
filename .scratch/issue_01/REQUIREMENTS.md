# Baseline startup dependency repair

Related issue: https://github.com/MrCCaesar/r3la/issues/1 (read on 2026-10-28).
The issue requires Go2 flat/rough baseline environments on IsaacLab 3.0.
This repair addresses the user's rough random-agent startup failure only.
No existing issue_01 requirements or test plan were present; issue_04 files
were already deleted in the user's working tree and are outside this repair.

- R1: Align the project's Newton override with the checked-out IsaacLab's
  explicit Newton revision, preserving reproducible dependency resolution.
- R2: The reported rough task with 16 environments and newton_gl must create,
  reset, step, and close successfully (bounded with --max_steps for verification).
- R3: Preserve task code, robot/terrain configuration, rewards, APIs, tests,
  and all pre-existing user changes.

## Baseline and impact analysis

Baseline: the reported command under GPU access fails in
isaaclab_newton/cloner/replicate.py:179 with
`TypeError: ModelBuilder.add_usd() got an unexpected keyword argument
'allow_unsafe_torch_checkpoints'`.
Project override/installed Newton: 71eeba16a717d4dcf0b9dd7056a7b6f863054dc3.
IsaacLab revision: 346c74fe7; its pyproject and Newton 11.0.0 changelog
require 42f7def118c2c4299ce493457bafd4e8a22a696e.
Installed add_usd signature lacks the keyword IsaacLab now passes.

- MUST CHANGE: pyproject.toml Newton override; matching Newton lock entries.
- MAY CHANGE: local installed Newton through uv synchronization; verification docs.
- MUST NOT CHANGE: task/MDP/robot/terrain/actuator code, test oracles, adjacent
  IsaacLab checkout, existing deleted issue_04 docs, untracked labs work, and
  unrelated pre-existing uv.lock edits.

No new shared state, public API, or concurrency change. Newton replacement can
affect simulation numerics/performance; startup smoke checks cannot establish
policy equivalence or real-time performance.
