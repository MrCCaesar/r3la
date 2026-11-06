"""CPU differential check of research validator, including exceptional metadata."""
import importlib.util
from dataclasses import replace
import torch
import subprocess
import sys
import types
from r3la.tasks.velocity.mdp.sensor_observations import read_low_rate_targets as candidate
baseline = types.ModuleType("baseline_sensor_observations")
sys.modules[baseline.__name__] = baseline
source = subprocess.check_output([
    "git", "show", "5768061:src/r3la/tasks/velocity/mdp/sensor_observations.py"
], text=True)
exec(compile(source, "baseline_sensor_observations.py", "exec"), baseline.__dict__)
original = baseline.read_low_rate_targets

spec = importlib.util.spec_from_file_location("sensor_test_helpers", "tests/test_parkour_sensors.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
torch.manual_seed(37)
env = helpers.sample_env()
fixtures = {name: sensor.sample for name, sensor in env.scene.items()}
for case in range(180):
    for index, (name, sensor) in enumerate(env.scene.items()):
        source = fixtures[name]
        captured = torch.tensor([(case + index) % 3 != 0, (case + index) % 4 != 0])
        time = torch.zeros(2)
        age = torch.zeros(2)
        episode = torch.zeros(2, dtype=torch.int64)
        if case >= 20 and index > 0:
            value = [0.0, 0.5e-6, 2e-6, float("nan"), float("inf")][(case + index) % 5]
            time[case % 2] = value
            age[(case + 1) % 2] = value
            if case % 7 == 0:
                episode[case % 2] = index
        sensor.sample = replace(source, captured=captured, capture_time=time, age=age, episode_id=episode)
    if case % 19 == 0:
        for sensor in env.scene.values():
            sensor.sample.capture_time[:] = float("inf")
            sensor.sample.age[:] = float("inf")
    if case >= 120:
        sensor = env.scene["fl_height_scanner"]
        change = case % 10
        if change == 0:
            sensor.sample = replace(sensor.sample, valid=torch.zeros(2, 1, dtype=torch.bool))
        elif change == 1:
            sensor.sample = replace(sensor.sample, values=sensor.sample.values.double())
        elif change == 2:
            sensor.sample = replace(sensor.sample, age=torch.zeros(2, device="meta"))
        elif change == 3:
            sensor.sample = replace(sensor.sample, episode_id=torch.zeros(2))
        elif change == 4:
            sensor.sample = replace(sensor.sample, captured=torch.zeros(2, 1, dtype=torch.bool))
        elif change == 5:
            first = env.scene["front_camera"]
            first.sample = replace(first.sample, episode_id=torch.zeros(2, 1, dtype=torch.int64))
        elif change == 6:
            sensor.sample = replace(sensor.sample, valid=sensor.sample.valid.float())
        elif change == 7:
            sensor.sample = replace(sensor.sample, values=sensor.sample.values[:, :1])
        elif change == 8:
            sensor.sample = replace(sensor.sample, age=torch.zeros(1))
        else:
            sensor.sample = replace(sensor.sample, values=torch.zeros(sensor.sample.values.shape, device="meta"))
    outcomes = []
    for fn in (original, candidate):
        try:
            outcomes.append(fn(env))
        except (ValueError, RuntimeError) as error:
            outcomes.append((type(error).__name__, str(error)))
    if isinstance(outcomes[0], tuple):
        assert outcomes[0] == outcomes[1], (case, outcomes)
    else:
        assert not isinstance(outcomes[1], tuple), (case, outcomes)
        for field in ("target", "metadata"):
            for key, value in getattr(outcomes[0], field).items():
                torch.testing.assert_close(value, getattr(outcomes[1], field)[key], rtol=0, atol=0, equal_nan=True)
print("PASS: 180 CPU cases match values, masks, metadata and exact exception type/message")
