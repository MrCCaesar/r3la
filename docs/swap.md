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

## Verified integration

Formal verification on 2026-11-07 used this task at r3la `60b5d90`, rsl_rl
`8b8c7ce` and IsaacLab `beb9301f5`. Two headless environments completed training
for two 24-step rollouts, full checkpoint restoration followed by one rollout,
and independent evaluation for 32 steps. Each phase finished within 23 seconds
of its 180-second limit and maintained the required 8 GiB RAM / 4 GiB VRAM headroom.
The three models updated with finite parameters; both optimizers and the runner
iteration restored exactly. Evaluation checked default mean actions and explicit
sampling. No performance target or real-robot validation is implied.

The maintained `tests/test_swap_profile.py` checks physical field selection,
configuration serialization and Hydra overrides without starting a simulation.
Both tests passed in the final integration suite. Use the versions above together;
the installed rsl-rl package shares the same version number as the working checkout.

Local detailed evidence remains in the parent rsl_rl repository under
`.scratch/issue_1/verification-review-fixed.md` and `verification/review-fixed/`
within that issue directory. The bounded simulation driver is retained there as
verification tooling; it is not required for the maintained configuration tests.
