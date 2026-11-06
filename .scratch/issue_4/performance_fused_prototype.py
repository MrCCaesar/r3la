"""Aligned native low-rate targets and metric scan observations."""

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class LowRateTargets:
    """Borrowed adapter tensors; clone at the trajectory collection boundary."""

    target: dict[str, torch.Tensor]
    metadata: dict[str, torch.Tensor]


_LOW_RATE = (
    ("depth_image", "depth_valid", "front_camera"),
    ("body_height_scan", "body_height_valid", "body_height_scanner"),
    ("lf_height_scan", "lf_height_valid", "fl_height_scanner"),
    ("rf_height_scan", "rf_height_valid", "fr_height_scanner"),
    ("lh_height_scan", "lh_height_valid", "rl_height_scanner"),
    ("rh_height_scan", "rh_height_valid", "rr_height_scanner"),
)

_SPATIAL_SHAPES = ((240, 320, 1), (286,), (25,), (25,), (25,), (25,))


def read_low_rate_targets(env) -> LowRateTargets:
    """Read native sensors and reject capture/reset misalignment, never reschedule."""
    samples = [env.scene[name].read_sample() for _, _, name in _LOW_RATE]
    first = samples[0]
    if first.episode_id.ndim != 1:
        raise ValueError("Low-rate episode_id must be int64 [N]")
    count, device = first.episode_id.shape[0], first.values.device
    for (key, _, _), sample, spatial in zip(_LOW_RATE, samples, _SPATIAL_SHAPES, strict=True):
        expected = (count, *spatial)
        if (
            sample.values.shape != expected
            or sample.values.dtype != torch.float32
            or sample.valid.shape != expected
            or sample.valid.dtype != torch.bool
        ):
            raise ValueError(f"{key} requires float32 values and bool mask of shape {expected}")
        for field, dtype in (
            (sample.capture_time, torch.float32),
            (sample.age, torch.float32),
            (sample.episode_id, torch.int64),
            (sample.captured, torch.bool),
        ):
            if field.shape != (count,) or field.dtype != dtype or field.device != device:
                raise ValueError(f"{key} has invalid sample metadata shape/dtype/device")
        if sample.values.device != device or sample.valid.device != device:
            raise ValueError(f"{key} sample values and mask must share the bundle device")
    # Research prototype: fixed-shape reductions, one host decision on success.
    # On failure re-enter the original validator to preserve exact error ordering.
    peers = samples[1:]
    episodes = torch.stack([s.episode_id for s in peers])
    captured = torch.stack([s.captured for s in peers])
    times = torch.stack([s.capture_time for s in peers])
    ages = torch.stack([s.age for s in peers])
    both = first.captured.unsqueeze(0) & captured
    equal_episode = (episodes == first.episode_id.unsqueeze(0)).all()
    close_time = (torch.isclose(times, first.capture_time.unsqueeze(0), atol=1e-6, rtol=0) | ~both).all()
    close_age = (torch.isclose(ages, first.age.unsqueeze(0), atol=1e-6, rtol=0) | ~both).all()
    if not bool(equal_episode & close_time & close_age):
        return _original_read(env)
    metadata = {mask: sample.valid for (_, mask, _), sample in zip(_LOW_RATE, samples, strict=True)}
    metadata.update(
        episode_id=first.episode_id,
        low_rate_capture_time=first.capture_time,
        low_rate_age=first.age,
        low_rate_valid=torch.stack([sample.captured for sample in samples]).all(dim=0),
    )
    return LowRateTargets(
        {key: sample.values for (key, _, _), sample in zip(_LOW_RATE, samples, strict=True)}, metadata
    )


from r3la.tasks.velocity.mdp.sensor_observations import read_low_rate_targets as _original_read
