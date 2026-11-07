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

## Local installation

Keep the r3la and rsl_rl checkouts in sibling directories. This project's
`pyproject.toml` explicitly depends on `rsl-rl-lib==5.5.1` and maps it to the
editable `../rsl_rl` checkout; `uv.lock` records that source. The registry release
has the same version but does not contain SWAPPPO. A one-off pip installation can
be replaced by `uv run` synchronization when the lockfile still names that release.

Run from the r3la directory:

```bash
uv sync --locked --inexact
uv run python -c 'import rsl_rl; from rsl_rl.utils import resolve_callable; print(rsl_rl.__file__); print(resolve_callable("SWAPPPO"))'
uv run isaaclab train --task R3la-SWAP-Parkour-UnitreeGo2 --num_envs 2
```

The import check must show the sibling rsl_rl checkout. No PYTHONPATH override
is required. The commands above fix package selection; they do not establish
new simulation acceptance.

IsaacLab must remain unchanged. Its earlier SWAP backend patches have been
withdrawn. Stock playback does not implement the approved `policy.observe`
lifecycle, and checkpoint-load mode selection also needs integration review.
Do not treat stock playback as verified SWAP evaluation. Full stateful policy
export is unsupported.

## Historical integration verification

The following results used the earlier modified IsaacLab checkout. They remain
historical evidence and do not establish acceptance with the reverted IsaacLab
baseline `346c74fe7`.

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
Both tests passed in that integration suite. The package-source configuration
above prevents the registry package from shadowing the working checkout.

Local detailed evidence remains in the parent rsl_rl repository under
`.scratch/issue_1/verification-review-fixed.md` and `verification/review-fixed/`
within that issue directory. The bounded simulation driver is retained there as
verification tooling; it is not required for the maintained configuration tests.
