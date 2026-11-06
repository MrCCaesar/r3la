# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Go2 profile serialization and current-frame physical selection without simulation."""

import json

import torch
from rsl_rl.utils.swap_layout import resolve_swap_layout
from tensordict import TensorDict

from isaaclab.utils import to_dict

from r3la.tasks.velocity.config.Unitree.agents.rsl_rl_ppo_cfg import UnitreeGo2SWAPPPORunnerCfg
from r3la.tasks.velocity.config.Unitree.agents.swap_layout import make_swap_layout


def test_config_roundtrip_and_latest_proprio_selection():
    """Exercise the declared playback or checkpoint contract."""
    cfg = to_dict(UnitreeGo2SWAPPPORunnerCfg())
    assert cfg["algorithm"]["class_name"] == "SWAPPPO"
    assert cfg["actor"]["hidden_dims"] == [128, 128]
    assert cfg["swap"]["world_model"]["k"] == 5
    assert json.loads(json.dumps(cfg["swap"])) == cfg["swap"]
    target = {
        key: torch.zeros(2, size)
        for key, size in [
            ("body_height_scan", 286),
            ("lf_height_scan", 25),
            ("rf_height_scan", 25),
            ("lh_height_scan", 25),
            ("rh_height_scan", 25),
        ]
    }
    target["depth_image"] = torch.ones(2, 240, 320, 1)
    obs = TensorDict(
        dict(
            proprio=torch.arange(210.0).repeat(2, 1),
            commands=torch.tensor([[1.0, 2.0, 3.0]]).repeat(2, 1),
            privilege=torch.zeros(2, 273),
            target=target,
        ),
        [2],
    )
    layout = resolve_swap_layout(
        {"inline": make_swap_layout(obs=obs, env=None)}, obs=obs, env=None, device="cpu", dtype=torch.float32
    )
    current = layout.world_observations(obs).proprio[0]
    assert current[:6].tolist() == [168.0, 169.0, 170.0, 171.0, 172.0, 173.0]
    assert current[6:9].tolist() == [1.0, 2.0, 3.0]
    assert current[-1] == 197
    assert layout.height.dim == 386
