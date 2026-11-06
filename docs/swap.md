# SWAP functional profile

`R3la-SWAP-Parkour-UnitreeGo2` uses the existing OnPolicyRunner with SWAPPPO.
The task-side `agents/swap_layout.py` declares the actual observation order,
latest WM proprio frame, joint action coordinates and physical mirror matrices.
Generic rsl-rl modules do not infer Go2 geometry. Actor/critic and WM have separate
optimizers; AMP is not enabled.

The config's `swap` dictionary round-trips through ordinary config serialization
and Hydra overrides. The numeric profile is only a functional validation starting
point: k=5, h/z=128/32, sequence length 5, rollout length 24. No paper-performance
or asset-symmetry validation is claimed.

Use the working rsl_rl checkout in PYTHONPATH; the installed package has the same
version number and may otherwise shadow this implementation. Normal playback
must use the updated IsaacLab backend, which calls policy.observe after env.step
and avoids a second done reset. Full stateful policy export is unsupported.

Real train/resume/evaluation belongs to the explicit Verify stage. Use two
environments, headless mode, the approved short run limits and resource checks.
The parent task's bounded driver is rsl_rl/.scratch/issue_1/verification/run_smoke.py;
it has not been executed during implementation.
