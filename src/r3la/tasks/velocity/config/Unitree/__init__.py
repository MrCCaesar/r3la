# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import gymnasium as gym

from . import agents

##
# Register Gym environments.
##

gym.register(
    id="R3la-SWAP-Parkour-UnitreeGo2",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "eval_env_cfg_entry_point": f"{__name__}.evaluation:make_parkour_evaluation_cfg",
        "env_cfg_entry_point": f"{__name__}.parkour_env_cfg:UnitreeGo2ParkourEnvCfg",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:UnitreeGo2SWAPPPORunnerCfg",
        "default_agent": "rsl_rl",
    },
)
