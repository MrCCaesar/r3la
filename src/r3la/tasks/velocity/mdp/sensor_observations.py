"""Metric observations from native held sensor samples."""

import torch


_TARGET_SENSORS = {
    "depth_image": "front_camera",
    "body_height_scan": "body_height_scanner",
    "lf_height_scan": "fl_height_scanner",
    "rf_height_scan": "fr_height_scanner",
    "lh_height_scan": "rl_height_scanner",
    "rh_height_scan": "rr_height_scanner",
}


def low_rate_target(env, key: str) -> torch.Tensor:
    """Read only the selected sensor's held values using its native scheduling."""
    return env.scene[_TARGET_SENSORS[key]].read_sample().values


def metric_height_scan(env, sensor_cfg) -> torch.Tensor:
    """Capture-time reference Z minus terrain Z, no clipping or launch offset."""
    return env.scene[sensor_cfg.name].read_sample().values
