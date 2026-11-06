# Metadata training relevance — interview

Status: Draft discussion; no metadata contract change approved. User invoked
grill-with-docs to ask whether MetadataCfg contents are needed for training.

## Confirmed facts

Metadata is a separate observation group. Current runner obs_groups does not select
it for actor/critic. That runner still references an absent policy group and is
not the completed SWAP learner/collector, so unused today does not establish
unnecessary in the intended training system. Approved interfaces delegate feature
selection, loss masks and training sequences to the downstream runner/model.

Depth and scan invalid samples are encoded as zero with separate boolean masks.
low_rate_valid means a post-reset aligned capture exists, NOT that it is newly
captured this step or that all pixels/rays are valid. After autoreset, returned
observations belong to the new episode. episode_id/time/age support lifecycle
tracking but can overlap a correctly implemented collector's own bookkeeping.
base_height_valid also exists in the AMP output, so export duplication is possible.

## Assessment / proposed terminology

Distinguish network input, loss validity mask, collection bookkeeping and debug
telemetry. A field may be useful for training without being fed into a network.
No evidence requires every metadata field to enter policy/critic input or be
stored for every50Hz transition. No metadata deletion follows from this interview.

## Current decision frontier

1. Invalid reconstruction targets: recommend use validity masks to exclude invalid
   depth/scan targets from loss; do not treat no-hit zero as a measured surface.
2. Collector responsibility: recommend collector owns10Hz sample selection and
   episode boundary handling; then evaluate which timing/identity fields it needs
   explicitly versus can derive from existing native step outputs.

## Deferred

Exact minimal export set, replay storage, per-network input layout, moving metadata
out of the observation manager and any code edits follow confirmed consumer
semantics. Keep existing internal cross-sensor validation until separately decided.

## Round 1 user decisions

1. User rejects masking invalid/error sensor targets out of reconstruction. The
   purpose is to encode current observed information in the world model and
   accelerate training, including sensor errors. Do not interpret this as an
   instruction to add new noise models or change current sensor encoding.
2. User rejects a sequence-collector requirement: intended RL data unit is a
   single transition (state, action, reward; next-state/termination handling to
   be specified where the loss consumes them), not sampled sequences. Earlier
   recommendation of a sequence-aware collector was not accepted.

## Revised assessment

Spatial masks are not needed to exclude reconstruction targets under the chosen
loss semantics. Metadata need not enter networks solely to support that masking.
Explicit episode IDs and sampling times have no demonstrated mandatory training
consumer for the stated single-transition/current-observation reconstruction use.
Internal validity checks and sample storage isolation serve environment correctness
and remain separate from exported training metadata. Standard termination and
truncation outputs remain relevant even to single-transition learning; this is
not a requirement for sequence sampling.

## Next frontier

Confirm reconstruction uses exactly the delivered target tensors, including
current zero encodings for invalid pixels/rays, without spatial-mask exclusion.
Then consider removing metadata observation export from normal training while
keeping native termination/truncation and internal alignment/validity mechanisms.
This remains a proposal; no observation schema changes made. Loss/prediction
architecture beyond current reconstruction remains unspecified, not inferred.

## Installed PPO implementation evidence

See `rsl-rl-training-data.md` (RSL-RL 5.5.1). Feedforward updates shuffle individual
transitions, while rollout and GAE still require temporal ordering. PPO also
stores old values/log probabilities/distribution parameters and derives advantages
and returns; state/action/reward alone are insufficient. Standard PPO has no
mandatory consumer for sensor metadata. However, selecting network groups does
not filter storage, and nested observation preservation is not guaranteed by the
current storage allocation. Current project MLP routing also requires adaptation.
No metadata export removal or training adapter implementation approved.

## User authorization and implementation

User subsequently requested removing unnecessary metadata exports and consistency
checks. Implemented the scope recorded in ADR-010: remove the observation group,
bundle/metadata APIs and cross-sensor validation; select one sensor per target.
Earlier statements that removal was unapproved are superseded by this request.
