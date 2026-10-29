# Startup repair test plan

- R1: Compare the override and lock revision to the adjacent IsaacLab
  pyproject; inspect installed direct_url and add_usd signature after uv sync.
  Oracle: IsaacLab's declared dependency and actual caller keyword.
  Negative control: old installed signature lacks that keyword and the
  unmodified startup fails with the captured TypeError.
- R2: Run the user's command with --max_steps 100 on the GPU, with newton_gl.
  Require exit 0 after creation/reset/steps/cleanup. Also smoke-test the flat
  baseline with 16 environments to cover the shared dependency.
- R3: Run existing pytest before/after; compare git diff and lock changes
  against the pre-repair working-tree copy at /tmp/r3la-uv-lock-before-newton-fix.
  Do not change expected results to conceal existing failures.
- Build the project; check uv lock consistency. Independent read-only review.

The ambient ROS pytest plugin currently fails to import lark; rerun repository
tests with PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 to isolate repository assertions.
Long training, numerical trajectory equivalence, latency/jitter/allocation
benchmarks, deadlines, and constraint metrics are outside this startup repair;
report these as unverified rather than infer them from successful launch.
