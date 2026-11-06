# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

__all__ = [
    "randomize_shared_material",
    "reset_parkour_state",
    "ParkourAttemptState",
    "ParkourCurriculum",
    "ParkourVelocityCommand",
    "ParkourVelocityCommandCfg",
    "validate_parkour_actions",
    "low_rate_target",
    "metric_height_scan",
    "amp_field",
    "terrain_relative_height",
    "feet_air_time",
    "base_height_l2",
    "flat_orientation_l2",
    "undesired_contacts",
    "is_contact",
    "actuator_gains",
    "com_offset",
    "link_mass",
    "foot_restitution",
    "foot_friction",
    "joint_pos_target_l2",
    "joint_deviation_l2",
    "joint_power",
    "stance_base_height_orientation_exp",
    "feet_stumble",
    "action_smoothness_l2",
]

# Forward stable MDP terms lazily, then override with environment-specific terms below.
from isaaclab.envs.mdp import *  # noqa: F401, F403

from isaaclab_tasks.core.velocity.mdp import *  # noqa: F401, F403

from .actions import validate_parkour_actions
from .terminations import ParkourAttemptState
from .commands import ParkourVelocityCommand, ParkourVelocityCommandCfg
from .curriculums import ParkourCurriculum
from .events import randomize_shared_material, reset_parkour_state
from .observations import (
    actuator_gains,
    amp_field,
    com_offset,
    foot_friction,
    foot_restitution,
    is_contact,
    link_mass,
    terrain_relative_height,
)
from .rewards import (
    action_smoothness_l2,
    base_height_l2,
    feet_air_time,
    feet_stumble,
    flat_orientation_l2,
    joint_deviation_l2,
    joint_pos_target_l2,
    joint_power,
    stance_base_height_orientation_exp,
    undesired_contacts,
)
from .sensor_observations import low_rate_target, metric_height_scan
