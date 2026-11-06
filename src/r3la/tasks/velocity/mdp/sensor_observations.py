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

_TARGET_INDEX = {key: index for index, (key, _, _) in enumerate(_LOW_RATE)}
_MASK_INDEX = {mask: index for index, (_, mask, _) in enumerate(_LOW_RATE)}

_SPATIAL_SHAPES = ((240, 320, 1), (286,), (25,), (25,), (25,), (25,))


def _read_validated_samples(env):
    """Read one fresh snapshot and validate native sample alignment."""
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
    peers = samples[1:]
    episodes = torch.stack([sample.episode_id for sample in peers])
    captured = torch.stack([sample.captured for sample in peers])
    times = torch.stack([sample.capture_time for sample in peers])
    ages = torch.stack([sample.age for sample in peers])
    both = first.captured.unsqueeze(0) & captured
    same_episode = (episodes == first.episode_id.unsqueeze(0)).all()
    same_time = (torch.isclose(times, first.capture_time.unsqueeze(0), atol=1e-6, rtol=0) | ~both).all()
    same_age = (torch.isclose(ages, first.age.unsqueeze(0), atol=1e-6, rtol=0) | ~both).all()
    if not bool(same_episode & same_time & same_age):
        # Diagnose the original error on these same samples, without another read.
        for sample in samples[1:]:
            if not torch.equal(sample.episode_id, first.episode_id):
                raise RuntimeError("Low-rate sensor reset identity mismatch")
            both = first.captured & sample.captured
            if not torch.allclose(sample.capture_time[both], first.capture_time[both], atol=1e-6, rtol=0):
                raise RuntimeError("Low-rate captures must be aligned; check substep/debug readers")
            if not torch.allclose(sample.age[both], first.age[both], atol=1e-6, rtol=0):
                raise RuntimeError("Low-rate sensor clocks must be aligned")
    return samples


def read_low_rate_targets(env) -> LowRateTargets:
    """Read native sensors and reject capture/reset misalignment, never reschedule."""
    samples = _read_validated_samples(env)
    first = samples[0]
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


def low_rate_target(env, key: str) -> torch.Tensor:
    """Observation-manager term selecting an approved target key."""
    samples = _read_validated_samples(env)
    return samples[_TARGET_INDEX[key]].values


def sensor_metadata(env, key: str) -> torch.Tensor:
    """Observation-manager term selecting timing or validity metadata."""
    if key == "critic_height_valid":
        return env.scene["terrain_height_scanner"].read_sample().valid
    samples = _read_validated_samples(env)
    if key in _MASK_INDEX:
        return samples[_MASK_INDEX[key]].valid
    if key == "low_rate_valid":
        return torch.stack([sample.captured for sample in samples]).all(dim=0)
    field = {"episode_id": "episode_id", "low_rate_capture_time": "capture_time", "low_rate_age": "age"}[key]
    return getattr(samples[0], field)


def metric_height_scan(env, sensor_cfg) -> torch.Tensor:
    """Capture-time reference Z minus terrain Z, no clipping or launch offset."""
    return env.scene[sensor_cfg.name].read_sample().values
