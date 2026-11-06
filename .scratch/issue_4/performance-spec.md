# Issue #4 — Performance and MDP organization specification

Status: **Approved** — user explicitly approved the detailed specification and
requested Plan via to-tickets on 2026-11-06.
The no-cross-call-cache direction and Specify entry were approved by user “yes”
to Q8 on 2026-11-06. Production implementation still requires its stage approval.

## Confirmed facts and scope

PF1. Baseline commit5768061, fixed native dependency346c74fe; four environments,
RGB+image-plane depth, full six-family terrain configuration. Research measured
34.3335881096 ms full-step and28.8038928638 ms observation median window means.
PF2. Scratch fused-check prototype measured13.7055292400 ms and8.6395656480 ms,
with16 sensor tests and120 differential cases passing. Production has not changed.
PF3. Sixteen observation selectors currently assemble the complete low-rate bundle;
the optimized selectors will no longer call that public bundle assembler.
PF4. User explicitly permits removal of mdp.attempts and requires the single
termination implementation and project imports to move to terminations.py while
retaining mdp.ParkourAttemptState and native lazy imports.

The implementation changes are limited to low-rate observation access/validation,
termination module ownership and directly dependent tests/documentation. There is
no new sensor clock/cache, manager/environment class, upstream patch, learner,
physics/terrain/randomization alteration or camera configuration change.

## PS1 — Validated snapshot access

In sensor_observations.py factor a private reader that calls all six native
read_sample methods once per invocation, in the existing _LOW_RATE order, then
validates and returns those same samples. Each selector invocation remains fresh;
there is no persistent sample/validation cache, step key or first-term dependency.
Native lazy scheduling and its capture/reset behavior remain authoritative.

Retain current validation order for all structural checks, including the first
sample episode_id rank check, per-sensor value/mask shapes and dtypes, metadata
shape/dtype/device checks, and consistent value/mask devices. Structural failures
raise the same ValueError message before any alignment fast path.

For the five peers, form fixed-shape [5,N] metadata tensors and combine:

- exact episode_id equality to the first sensor for every row;
- capture_time closeness only where first.captured AND peer.captured;
- age closeness under the same eligibility mask.

Time comparisons use torch.isclose(atol=1e-6, rtol=0), masked using logical OR
with ineligible rows. NaN remains unequal for eligible rows, matching allclose;
equal infinities follow native isclose/allclose behavior. All-ineligible and empty
row sets retain the original vacuous comparison behavior. No boolean-indexed
variable-length tensors are needed on the successful alignment path.

Reduce the combined result to one host-visible validity decision. This describes
the alignment validator only, not all synchronization inside native sensor reads.
On success return the samples. On failure run the original per-peer checks over
these SAME samples, ordered peer-by-peer: episode identity, capture_time, age.
Raise the original RuntimeError type/message for the first failure. Do not re-read
sensors, schedule an extra capture or recursively call the public bundle reader.
This slow diagnostic path preserves failure precedence without slowing valid reads.

## PS2 — Public interfaces and selection

These remain project APIs, implemented in sensor_observations.py and exposed via
current mdp exports. No public signatures or output contracts change.

| API | Input | Output and ownership | Behavior |
|---|---|---|---|
| read_low_rate_targets(env) | native env/scene exposing six low-rate sample providers | LowRateTargets(target, metadata); existing ordered keys/shapes/dtypes; borrowed sensor storage and freshly derived aggregates | Call validated reader once, assemble the full documented bundle |
| low_rate_target(env, key: str) | one of the six existing target keys | selected float32 tensor, metres, unchanged spatial shape/frame | Call validated reader once, return only the selected sample.values; do not build full target/metadata dictionaries |
| sensor_metadata(env, key: str) | existing mask/timing/episode/valid keys | bool mask/captured aggregate, float32 seconds, or int64 episode IDs as currently documented | Return only requested field; aggregate all captured flags only for low_rate_valid |
| sensor_metadata(env, "critic_height_valid") | critic scanner present | critic bool mask [N,187] | Preserve existing direct critic-only read; no low-rate bundle validation |
| metric_height_scan(env, sensor_cfg) | existing SceneEntityCfg selecting scanner | float32 capture-reference height in metres | Unchanged |

Target shapes are depth[N,240,320,1], body[N,286], each foot[N,25]. Matching
validity masks have identical shapes. Episode/capture_time/age/captured-derived
metadata are[N]. Native frame and height conventions remain in interfaces.md.
Unknown non-critic keys still raise KeyError AFTER the existing low-rate validation
would have run; no silent fallback or new alias. Values/masks must not be copied,
normalized, clipped or altered here. Existing ObservationManager cloning/history/
noise behavior remains unchanged. Retaining callers must clone borrowed data.

Static key-to-index lookups may be module constants. They contain no env/sample
state. Since all six sensors are still validated on each selector invocation,
expected low-rate read count remains96 per full observation. The reduction is
fewer GPU/CPU synchronization points and no unrequested full-bundle assembly, not
fewer physical captures or a promise of one shared read per step.

## PS3 — Lifecycle and numerical equivalence

- Repeated reads within one step can observe intervening reset/metadata mutation;
  no stale cached bundle can conceal it.
- Same-step reset, reset_to, partial reset, scene updates, direct public reads,
  constructor probes and compute_group retain current behavior.
- Return existing sampled tensors unchanged. For equivalent input snapshots,
  values/masks/metadata match exactly (equal NaNs for comparison where appropriate).
- Validation comparisons retain the existing1e-6 timing tolerance; do not relax
  acceptance thresholds or alter exception ordering to obtain a speedup.
- Discrete episode IDs, captured flags, termination and curriculum decisions,
  shapes, units, sample ages and observation histories must remain identical.
- Physics itself is untouched. Native calibration/lifecycle checks retain their
  existing tolerances; do not demand bitwise reproducibility across independent
  GPU simulation launches or use such nondeterminism to relax snapshot equivalence.

## PS4 — Termination ownership and readability

Move the sole ParkourAttemptState class, unchanged in behavior, to
src/r3la/tasks/velocity/mdp/terminations.py. Delete attempts.py; no compatibility
shim. Update mdp/__init__.pyi and tests/test_parkour_attempt.py direct import.
The lazy_export() implementation and public mdp.ParkourAttemptState remain.
Task configuration keeps DoneTerm(func=mdp.ParkourAttemptState). Curriculum keeps
accessing the existing instance through termination_manager term configuration;
no duplicate instance, reset callback or transition counter is introduced.

Keep sensor_observations.py as the cohesive sensor observation adapter; no
unrelated merge into observations.py is required. Existing actions, commands,
rewards, events and curriculum modules already have matching responsibilities.
Only other demonstrated ownership errors within this scope should be proposed;
no blanket file renaming or opportunistic cleanup.

## PS5 — Acceptance criteria

A1. Unit/differential tests preserve values, masks and metadata, including valid
and malformed shapes/dtypes/devices, uncaptured rows, empty eligible sets,
NaN/Inf, timing tolerance boundaries and simultaneous alignment errors.
A2. Selector tests show each selector returns the corresponding public-bundle
field without constructing the bundle; ordinary selectors still reject bad peer
metadata and invalid keys retain error ordering. Critic read remains separate.
A3. Full regression suite passes; termination tests use the new direct path and
public lazy export resolves to that same class. No src/tests references to old
mdp.attempts remain, and no eager simulation import is introduced.
A4. Native sensor check retains10Hz holds,50Hz critic, partial reset isolation,
calibration and RGB/debug outputs. Existing bounded native dynamics/curriculum
check validates termination ownership and pre-reset lifecycle after relocation.
A5. Re-run benchmark_performance.py in its unpatched/baseline mode against final
production code, with the identical approved four-env workload and timing method.
Record raw five100-step windows after50 warmup steps, capture/hold/reset categories
and5 explicit partial resets. Do not substitute the scratch prototype result.
A6. Full-step median window mean <=24.0335116767 ms AND observation median window
mean <=20.1627250047 ms (each70% of baseline). Report both reductions separately.
If targets fail or measurements are unstable, investigate and report; do not change
workload, weighting or semantics to claim success.
A7. Record exact commands/results/limitations, compileall and diff checks. No full
training, concurrent simulations, commit, push or issue edits are implied.

## Assumptions, open items and deferred work

Assumption: installed dependency and hardware remain fixed; record any change
before comparing results. Four-env zero-action results do not establish throughput
at training scale or successful traversal of all six families. The unchanged
terrain scene contains six families; active columns remain[0,4,9,14].

Detailed Specify contract and Plan entry are now approved. No remaining
user-facing architecture alternative is silently selected: no-cache direction,
partial bundle selection and removal of old import were explicitly approved.
Implementation sequencing belongs to Plan; cross-call caching and broader
performance work remain out of scope unless the measured final result warrants
a separately approved change.
