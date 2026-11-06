"""Approved calibration and low-rate sample boundary contracts."""

import math
from dataclasses import replace
from types import SimpleNamespace

import pytest
import torch

from isaaclab.utils.math import quat_apply

from r3la.labs.sensors import HeldDepthCameraCfg
from r3la.labs.sensors.sample import SensorSample
from r3la.tasks.velocity.config.Unitree.parkour_env_cfg import UnitreeGo2ParkourEnvCfg
from r3la.tasks.velocity.mdp.sensor_observations import low_rate_target


def test_depth_calibration_maps_optical_axes_to_base_and_has_square_pixels():
    cfg = HeldDepthCameraCfg(prim_path="/World/Robot/base/front_camera")
    assert (cfg.height, cfg.width) == (240, 320)
    assert cfg.offset.pos == (0.35, 0.0, 0.05) and cfg.offset.convention == "ros"
    axes = quat_apply(torch.tensor(cfg.offset.rot).repeat(3, 1), torch.eye(3))
    torch.testing.assert_close(axes, torch.tensor([[0.0, -1.0, 0.0], [0.0, 0.0, -1.0], [1.0, 0.0, 0.0]]))
    assert math.isclose(2 * math.atan(cfg.spawn.horizontal_aperture / (2 * cfg.spawn.focal_length)), math.radians(87))
    assert math.isclose(cfg.spawn.vertical_aperture / cfg.spawn.horizontal_aperture, 240 / 320)
    assert cfg.spawn.clipping_range == (0.1, 5.0)
    assert cfg.update_period == 0.1 and cfg.update_latest_camera_pose
    assert cfg.data_types == ["distance_to_image_plane"]


def test_configured_grids_have_approved_order_reach_periods_and_no_debug_readers():
    cfg = UnitreeGo2ParkourEnvCfg()
    for name, count, period in (
        ("terrain", 187, 0.02),
        ("body", 286, 0.1),
        ("fl", 25, 0.1),
        ("fr", 25, 0.1),
        ("rl", 25, 0.1),
        ("rr", 25, 0.1),
    ):
        sensor = getattr(cfg.scene, name + "_height_scanner")
        starts, directions = sensor.pattern_cfg.func(sensor.pattern_cfg, "cpu")
        assert starts.shape == (count, 3)
        assert sensor.pattern_cfg.ordering == "xy" and starts[1, 0] > starts[0, 0]
        assert starts[1, 1] == starts[0, 1]
        assert sensor.offset.pos == (0.0, 0.0, 2.0) and sensor.max_distance == 5
        assert sensor.update_period == period and sensor.global_world_only and not sensor.debug_vis
        assert sensor.heading_prim_path == "{ENV_REGEX_NS}/Robot/base"
        assert torch.all(directions[:, 2] == -1)


class SampleSensor:
    """External sensor boundary supplies already captured metric samples."""

    def __init__(self, shape):
        self.sample = SensorSample(
            torch.full((2, *shape), 1.75),
            torch.ones(2, *shape, dtype=torch.bool),
            torch.tensor([0.0, 0.1]),
            torch.tensor([0.04, 0.06]),
            torch.tensor([2, 1]),
            torch.tensor([True, True]),
        )

    def read_sample(self):
        return self.sample


def sample_env():
    names = (
        "front_camera",
        "body_height_scanner",
        "fl_height_scanner",
        "fr_height_scanner",
        "rl_height_scanner",
        "rr_height_scanner",
    )
    shapes = ((240, 320, 1), (286,), (25,), (25,), (25,), (25,))
    return SimpleNamespace(scene={name: SampleSensor(shape) for name, shape in zip(names, shapes, strict=True)})


@pytest.mark.parametrize("extra", ["rgb", "rgba", "rgb_hdr", "albedo", "depth", "distance_to_camera", "normals", "semantic_segmentation", "instance_segmentation"])
def test_held_depth_camera_accepts_native_debug_outputs(monkeypatch, extra):
    from isaaclab.sensors.camera import Camera
    from r3la.labs.sensors.camera import HeldDepthCamera

    cfg = HeldDepthCameraCfg(prim_path="/World/camera", data_types=["distance_to_image_plane", extra])
    received = []
    monkeypatch.setattr(Camera, "__init__", lambda self, config: received.append(config))
    monkeypatch.setattr(Camera, "__del__", lambda self: None)
    HeldDepthCamera(cfg)
    assert received == [cfg]  # Forward unchanged to native capability validation.


def test_held_depth_camera_requires_training_depth_even_with_debug_outputs():
    from r3la.labs.sensors.camera import HeldDepthCamera

    cfg = HeldDepthCameraCfg(prim_path="/World/camera", data_types=["rgb"])
    with pytest.raises(ValueError, match="Use CameraCfg"):
        HeldDepthCamera.__init__(SimpleNamespace(), cfg)


@pytest.mark.parametrize("key,name", [
    ("depth_image", "front_camera"),
    ("body_height_scan", "body_height_scanner"),
    ("lf_height_scan", "fl_height_scanner"),
    ("rf_height_scan", "fr_height_scanner"),
    ("lh_height_scan", "rl_height_scanner"),
    ("rh_height_scan", "rr_height_scanner"),
])
def test_target_reads_only_selected_sensor_and_sees_replacement(key, name):
    env = sample_env()
    sensor = env.scene[name]
    # Unrelated sensors need not be available or share capture metadata.
    env.scene = {name: sensor}
    sensor.sample.values[0] = 0  # Preserve encoded sensor errors for reconstruction.
    assert low_rate_target(env, key) is sensor.sample.values
    sensor.sample = replace(sensor.sample, values=torch.full_like(sensor.sample.values, 2.5))
    assert low_rate_target(env, key) is sensor.sample.values
    with pytest.raises(KeyError):
        low_rate_target(env, "unknown")


def test_training_config_has_no_metadata_export():
    cfg = UnitreeGo2ParkourEnvCfg()
    assert not hasattr(cfg.observations, "metadata")


def test_empty_target_preserves_shape():
    env = sample_env()
    sensor = env.scene["body_height_scanner"]
    sensor.sample = replace(sensor.sample, values=sensor.sample.values[:0])
    assert low_rate_target(env, "body_height_scan").shape == (0, 286)
