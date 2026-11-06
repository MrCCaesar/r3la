# RSL-RL PPO training data investigation

Status: Research findings; no production interface changes approved.

## Scope and evidence

Inspected installed `rsl-rl-lib==5.5.1` using repository `.venv/bin/python`.
RSL-RL source root: `.venv/lib/python3.12/site-packages/rsl_rl/`.
IsaacLab wrapper: `/home/sevnce-mr/IsaacLab/source/isaaclab_rl/isaaclab_rl/rsl_rl/vecenv_wrapper.py`.
No training or simulation launched.

## Confirmed data flow

`runners/on_policy_runner.py:79-108`: collect T steps across N environments,
then compute returns and update. The rollout need not contain complete episodes.
The wrapper returns `(TensorDict observations, rewards, dones, extras)`.
Observation batch size is `[N]`; done combines terminated and truncated.
For non-finite-horizon environments, extras includes `time_outs`.
Environment auto-reset means returned observations on done rows are reset observations.

`algorithms/ppo.py:124-164`: before stepping, PPO records observations, sampled
actions, old values, action log probabilities, distribution parameters and optional
recurrent states. After stepping, it records rewards and dones. Arbitrary extras
are not automatically stored. Logger consumes episode/log statistics separately.
Optional RND can modify rewards. Actual timeout correction in this version is
`reward += gamma * V(obs_t) * timeout`, using the saved current value; it does not
explicitly evaluate a terminal next observation in this path.

`algorithms/ppo.py:166-191`: final obs is evaluated for bootstrap; reverse temporal
recursion computes GAE advantages and returns using rewards, dones and values.
No separate next-observation buffer is stored for standard PPO.

## Storage and minibatches

`storage/rollout_storage.py:125-170,173-205,225-300`:

| Field | Rollout shape | Source |
| --- | --- | --- |
| Each tensor observation group | `[T,N,*features]` | Environment |
| Actions | `[T,N,A]` | Actor |
| Rewards, dones | `[T,N,1]` | Environment, with PPO reward processing |
| Old values, old log probabilities | `[T,N,1]` | Critic/actor |
| Distribution parameters | e.g. Gaussian `[T,N,A]` per parameter | Actor |
| Returns, advantages | `[T,N,1]` | GAE/return calculation |
| Recurrent hidden states | Architecture-dependent | Recurrent models only |

Feedforward PPO flattens `[T,N]` to `[T*N]`, shuffles transitions, and yields
observations, actions, old values, advantages, returns, old log probabilities and
old distribution parameters. Raw rewards/dones have already served target
calculation and are not yielded in this update batch. Recurrent PPO instead
splits/pads trajectories and supplies valid-step masks and initial hidden states.

Thus independent-transition neural updates do not remove the temporal rollout
needed for GAE. State/action/reward alone do not describe the PPO training batch.
Episode IDs, sensor timestamps/ages and sensor validity masks are not mandatory
standard PPO fields. Termination masks and recurrent padding masks are distinct
from sensor validity masks.

## Observation routing and current project limitations

`algorithms/ppo.py:434-455` selects actor/critic groups but passes the complete
observation TensorDict to storage. `models/mlp_model.py:110-118,179-189` requires
selected groups to be tensors `[N,D]`, concatenated in configured order.
Unused observation groups are not automatically removed before storage.

Current `src/r3la/tasks/velocity/config/Unitree/agents/rsl_rl_ppo_cfg.py` selects
actor `proprio,target`, critic `policy`. Current environment target is nonconcatenated
and includes images; `policy` is absent. These require an explicitly designed
training adapter/model, not a claim that current MLP configuration already trains
SWAP. No adapter or model change is authorized by this investigation.
The config has T=24, 4 minibatches and 5 epochs. With N=4, this would produce
96 transition slots and minibatches of 24 transitions, once compatibility is resolved.

CPU storage experiment using `.venv/bin/python`: flat TensorDict with actor and
unused keys retains both; copying works. For a nested metadata TensorDict with
boolean mask `[2,3]`, allocation produces a plain metadata tensor `[4,2]` instead
of nested mask `[4,2,3]`. Copy does not raise, but returns `[False,False]`, not the
source mask. Therefore absence of an exception does not establish correct nested
observation preservation in this storage implementation. This minimal experiment
is not an end-to-end project training test.

## Consequences and open decisions

User confirmed reconstruction should include actual delivered sensor errors and
should not exclude targets using validity masks. Standard PPO does not establish
a need for MetadataCfg. Removing its exported observation group remains proposed,
not approved; internal sensor alignment/validity checks are a separate concern.
Additional world-model losses may need other fields; their contract cannot be
inferred from standard PPO alone. Actual training input selection, image encoding
and auxiliary loss integration remain to be specified before implementation.
