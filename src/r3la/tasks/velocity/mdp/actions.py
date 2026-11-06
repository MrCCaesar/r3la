"""Explicit validation for untrusted actions, retaining the official action term."""

import torch


def validate_parkour_actions(env, actions: torch.Tensor) -> None:
    """Check the approved finite float32[N,12] contract without coercion.

    Call at an input/verification boundary. This is deliberately not inserted in
    every native step: checking GPU finiteness requires a host synchronization.
    ManagerBasedRLEnv itself permits device transfer and some broadcasting, so
    callers handling untrusted inputs must invoke this check before env.step().
    """
    if not isinstance(actions, torch.Tensor):
        raise TypeError("parkour actions must be a float32 torch.Tensor")
    expected = (env.num_envs, 12)
    if tuple(actions.shape) != expected:
        raise ValueError(f"parkour action shape must be {expected}, received {tuple(actions.shape)}")
    if actions.dtype != torch.float32:
        raise TypeError(f"parkour actions must be float32, received {actions.dtype}")
    if actions.device != torch.device(env.device):
        raise ValueError(f"parkour action device must be {env.device}, received {actions.device}")
    if not bool(torch.isfinite(actions).all()):
        raise ValueError("parkour actions must contain only finite values")
