# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for the Unitree Go2 velocity-tracking environment on rough terrain."""

"""Base configuration for the velocity-tracking locomotion environments on rough terrain."""

import math
from dataclasses import MISSING

from isaaclab.envs.mdp import last_action
from isaaclab_newton.physics import (
    KaminoPADMMSolverCfg,
    MJWarpSolverCfg,
    NewtonCfg,
    NewtonCollisionPipelineCfg,
    NewtonShapeCfg,
)
from isaaclab_ov.physics import OvPhysxCfg
from isaaclab_physx.physics import PhysxCfg

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import CurriculumTermCfg as CurrTerm
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.physics import PhysxAutoCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg, ContactSensorCfg, RayCasterCfg, patterns
from isaaclab.markers.config import RAY_CASTER_MARKER_CFG
from isaaclab.sim import SimulationCfg
from isaaclab_newton.renderers import NewtonWarpRendererCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.terrains.config.rough import ROUGH_TERRAINS_CFG
from isaaclab.utils import configclass, replace
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR, ISAACLAB_NUCLEUS_DIR
from isaaclab.utils.noise import UniformNoiseCfg as Unoise

from isaaclab_tasks.utils import PresetCfg

##
# Task specific settings
##


import r3la.tasks.velocity.mdp as mdp
from r3la.labs.terrains import PARKOUR_TERRAINS_CFG
# UNITREE_GO2_CFG.init_state.pos is (0, 0, 0.4) -- the asset's own authored standing height.
from isaaclab_assets.robots.unitree import UNITREE_GO2_CFG


_GO2_STANDING_HEIGHT = 0.4
_HEIGHT_SCANNER_DEBUG_VIS = True
_FOOT_HEIGHT_SCANNER_OFFSET = 0.5
_OBSERVATION_HISTORY_LENGTH = 4
_SYMMETRY_JOINT_NAMES = ['FL_hip_joint', 'FL_thigh_joint', 'FL_calf_joint', 
                         'FR_hip_joint', 'FR_thigh_joint', 'FR_calf_joint', 
                         'RL_hip_joint', 'RL_thigh_joint', 'RL_calf_joint', 
                         'RR_hip_joint', 'RR_thigh_joint', 'RR_calf_joint']


##
# Physics backend presets
##


@configclass
class RoughPhysicsCfg(PresetCfg):
    """Shared backend presets for locomotion velocity environments."""

    isaacsim_physx = PhysxCfg(gpu_max_rigid_patch_count=10 * 2**15)
    ovphysx = OvPhysxCfg(gpu_max_rigid_patch_count=10 * 2**15)
    physx = PhysxAutoCfg(isaacsim_physx=isaacsim_physx, ovphysx=ovphysx)
    newton_mjwarp = NewtonCfg(
        solver_cfg=MJWarpSolverCfg(
            njmax=1000,
            nconmax=300,
            cone="pyramidal",
            impratio=1.0,
            integrator="implicitfast",
            use_mujoco_contacts=False,
        ),
        collision_cfg=NewtonCollisionPipelineCfg(max_triangle_pairs=2_500_000),
        num_substeps=2,
        debug_mode=False,
        default_shape_cfg=NewtonShapeCfg(margin=0.0, ke=160000.0, kd=1100.0),
    )
    newton_kamino = NewtonCfg(solver_cfg=KaminoPADMMSolverCfg(max_contacts_per_world=64))
    default = newton_mjwarp


##
# Scene definition
##


@configclass
class ParkourSceneCfg(InteractiveSceneCfg):
    """Configuration for the terrain scene with a legged robot."""
    
    # ground terrain
    terrain = TerrainImporterCfg(
        prim_path="/World/ground",
        terrain_type="generator",
        terrain_generator=PARKOUR_TERRAINS_CFG,
        max_init_terrain_level=5,
        collision_group=-1,
        physics_material=sim_utils.PhysxRigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
        ),
        visual_material=sim_utils.MdlFileCfg(
            mdl_path=f"{ISAACLAB_NUCLEUS_DIR}/Materials/TilesMarbleSpiderWhiteBrickBondHoned/TilesMarbleSpiderWhiteBrickBondHoned.mdl",
            project_uvw=True,
            texture_scale=(0.25, 0.25),
        ),
        debug_vis=False,
    )
    # robots
    robot: ArticulationCfg = UNITREE_GO2_CFG.replace(
        prim_path="{ENV_REGEX_NS}/Robot"
    )
    # sensors: the concrete implementation is selected automatically from the active physics backend;
    # backend-specific fields such as ``global_world_only`` are ignored by the backends that do not use them
    front_camera = CameraCfg(
            prim_path="{ENV_REGEX_NS}/Robot/base/front_camera",
            update_period=0.1,
            height=240,
            width=320,
            data_types=["rgb", "distance_to_image_plane"],
            spawn=sim_utils.PinholeCameraCfg(
                focal_length=24.0, focus_distance=400.0, horizontal_aperture=20.955, clipping_range=(0.1, 1.0e5)
            ),
            offset=CameraCfg.OffsetCfg(pos=(0.0, 0.0, 0.015), rot=(0.0, 0.0, 0.0, 0.0), convention="ros"),
            renderer_cfg=NewtonWarpRendererCfg()
        )
    terrain_height_scanner = RayCasterCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base",
        offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 20.0)),
        ray_alignment="yaw",
        pattern_cfg=patterns.GridPatternCfg(resolution=0.1, size=[1.6, 1.0]),
        debug_vis=_HEIGHT_SCANNER_DEBUG_VIS,
        visualizer_cfg=replace(
            RAY_CASTER_MARKER_CFG, 
            prim_path="/Visuals/terrain_height_scanner",
            markers={
                    "hit": sim_utils.SphereCfg(
                        radius=0.04,
                        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.0, 0.0)),
                    ),
                },
        ),
        mesh_prim_paths=["/World/ground"],
        global_world_only=True,
    )
    body_height_scanner = RayCasterCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base",
        offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 0.0)),
        ray_alignment="yaw",
        pattern_cfg=patterns.GridPatternCfg(resolution=0.05, size=[1.05, 0.6]),
        debug_vis=_HEIGHT_SCANNER_DEBUG_VIS,
        visualizer_cfg=replace(
            RAY_CASTER_MARKER_CFG, 
            prim_path="/Visuals/terrain_height_scanner",
            markers={
                    "hit": sim_utils.SphereCfg(
                        radius=0.02,
                        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 1.0, 0.0)),
                    ),
                },
        ),
        mesh_prim_paths=["/World/ground"],
        global_world_only=True,
    )
    fl_height_scanner = RayCasterCfg(
            prim_path="{ENV_REGEX_NS}/Robot/FL_foot",
            offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, _FOOT_HEIGHT_SCANNER_OFFSET)),
            ray_alignment="yaw",
            pattern_cfg=patterns.GridPatternCfg(resolution=0.05, size=[0.2, 0.2]),
            debug_vis=_HEIGHT_SCANNER_DEBUG_VIS,
            visualizer_cfg=replace(
                RAY_CASTER_MARKER_CFG, 
                prim_path="/Visuals/fl_height_scanner",
                markers={
                        "hit": sim_utils.SphereCfg(
                            radius=0.02,
                            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 0.0, 1.0)),
                        ),
                    },
            ),
            mesh_prim_paths=["/World/ground"],
            global_world_only=True,
        )
    fr_height_scanner = RayCasterCfg(
            prim_path="{ENV_REGEX_NS}/Robot/FR_foot",
            offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, _FOOT_HEIGHT_SCANNER_OFFSET)),
            ray_alignment="yaw",
            pattern_cfg=patterns.GridPatternCfg(resolution=0.05, size=[0.2, 0.2]),
            debug_vis=_HEIGHT_SCANNER_DEBUG_VIS,
            visualizer_cfg=replace(
                RAY_CASTER_MARKER_CFG, 
                prim_path="/Visuals/fr_height_scanner",
                markers={
                        "hit": sim_utils.SphereCfg(
                            radius=0.02,
                            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 0.0, 1.0)),
                        ),
                    },
            ),
            mesh_prim_paths=["/World/ground"],
            global_world_only=True,
        )
    rl_height_scanner = RayCasterCfg(
            prim_path="{ENV_REGEX_NS}/Robot/RL_foot",
            offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, _FOOT_HEIGHT_SCANNER_OFFSET)),
            ray_alignment="yaw",
            pattern_cfg=patterns.GridPatternCfg(resolution=0.05, size=[0.2, 0.2]),
            debug_vis=_HEIGHT_SCANNER_DEBUG_VIS,
            visualizer_cfg=replace(
                RAY_CASTER_MARKER_CFG, 
                prim_path="/Visuals/rl_height_scanner",
                markers={
                        "hit": sim_utils.SphereCfg(
                            radius=0.02,
                            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 0.0, 1.0)),
                        ),
                    },
            ),
            mesh_prim_paths=["/World/ground"],
            global_world_only=True,
        )
    rr_height_scanner = RayCasterCfg(
            prim_path="{ENV_REGEX_NS}/Robot/RR_foot",
            offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, _FOOT_HEIGHT_SCANNER_OFFSET)),
            ray_alignment="yaw",
            pattern_cfg=patterns.GridPatternCfg(resolution=0.05, size=[0.2, 0.2]),
            debug_vis=_HEIGHT_SCANNER_DEBUG_VIS,
            visualizer_cfg=replace(
                RAY_CASTER_MARKER_CFG, 
                prim_path="/Visuals/rr_height_scanner",
                markers={
                        "hit": sim_utils.SphereCfg(
                            radius=0.02,
                            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 0.0, 1.0)),
                        ),
                    },
            ),
            mesh_prim_paths=["/World/ground"],
            global_world_only=True,
        )
    contact_forces = ContactSensorCfg(prim_path="{ENV_REGEX_NS}/Robot/[^/]*", history_length=3, track_air_time=True)
    # lights
    sky_light = AssetBaseCfg(
        prim_path="/World/skyLight",
        spawn=sim_utils.DomeLightCfg(
            intensity=750.0,
            texture_file=f"{ISAAC_NUCLEUS_DIR}/Materials/Textures/Skies/PolyHaven/kloofendal_43d_clear_puresky_4k.hdr",
        ),
    )


##
# MDP settings
##


@configclass
class CommandsCfg:
    """Command specifications for the MDP."""

    base_velocity = mdp.UniformVelocityCommandCfg(
        asset_name="robot",
        resampling_time_range=(10.0, 10.0),
        rel_standing_envs=0.02,
        rel_heading_envs=1.0,
        heading_command=True,
        heading_control_stiffness=0.5,
        debug_vis=True,
        ranges=mdp.UniformVelocityCommandCfg.Ranges(
            lin_vel_x=(-1.0, 1.0), lin_vel_y=(-1.0, 1.0), ang_vel_z=(-1.0, 1.0), heading=(-math.pi, math.pi)
        ),
    )


@configclass
class ActionsCfg:
    """Action specifications for the MDP."""

    joint_pos = mdp.JointPositionActionCfg(
            asset_name="robot", 
            joint_names=_SYMMETRY_JOINT_NAMES, 
            scale=0.5,
            preserve_order=True, 
            use_default_offset=True
        )


@configclass
class ObservationsCfg:
    """Observation specifications for the MDP."""

    @configclass
    class TargetCfg(ObsGroup):
        """Observations for reconstruction target."""

        ### Body and foot heightmap
        body_height_scan = ObsTerm(
            func=mdp.height_scan,
            params={"sensor_cfg": SceneEntityCfg("body_height_scanner"), "offset": 0.0},
            clip=(-1.0, 1.0),
        )
        lf_height_scan = ObsTerm(
            func=mdp.height_scan,
            params={"sensor_cfg": SceneEntityCfg("fl_height_scanner"), "offset": _FOOT_HEIGHT_SCANNER_OFFSET},
            clip=(-1.0, 1.0),
        )
        rf_height_scan = ObsTerm(
            func=mdp.height_scan,
            params={"sensor_cfg": SceneEntityCfg("fr_height_scanner"), "offset": _FOOT_HEIGHT_SCANNER_OFFSET},
            clip=(-1.0, 1.0),
        )
        lh_height_scan = ObsTerm(
            func=mdp.height_scan,
            params={"sensor_cfg": SceneEntityCfg("rl_height_scanner"), "offset": _FOOT_HEIGHT_SCANNER_OFFSET},
            clip=(-1.0, 1.0),
        )
        rh_height_scan = ObsTerm(
            func=mdp.height_scan,
            params={"sensor_cfg": SceneEntityCfg("rr_height_scanner"), "offset": _FOOT_HEIGHT_SCANNER_OFFSET},
            clip=(-1.0, 1.0),
        )
        ### depth image
        depth_image = ObsTerm(
            func=mdp.image_depth,
            params={"sensor_cfg": SceneEntityCfg("front_camera")},

        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False

        
    @configclass
    class PropriceptionCfg(ObsGroup):
        """Observations for policy group."""

        # observation terms (order preserved)
        base_ang_vel = ObsTerm(func=mdp.base_ang_vel, noise=Unoise(n_min=-0.2, n_max=0.2))
        projected_gravity = ObsTerm(
            func=mdp.projected_gravity,
            noise=Unoise(n_min=-0.05, n_max=0.05),
        )
        joint_pos = ObsTerm(func=mdp.joint_pos_rel, 
                            params={"asset_cfg": SceneEntityCfg("robot", joint_names=_SYMMETRY_JOINT_NAMES)},
                            noise=Unoise(n_min=-0.01, n_max=0.01))
        joint_vel = ObsTerm(func=mdp.joint_vel_rel, 
                            params={"asset_cfg": SceneEntityCfg("robot", joint_names=_SYMMETRY_JOINT_NAMES)},
                            noise=Unoise(n_min=-1.5, n_max=1.5))
        last_actions = ObsTerm(func=mdp.last_action)

        def __post_init__(self):
            self.enable_corruption = True
            self.concatenate_terms = True
            self.history_length = _OBSERVATION_HISTORY_LENGTH
            self.flatten_history_dim = True
            self.history_order = "time"

    @configclass
    class CommandObsCfg(ObsGroup):
        """Observation for command"""
        velocity_commands = ObsTerm(func=mdp.generated_commands, params={"command_name": "base_velocity"})

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class PrivilegCfg(ObsGroup):
        """Observations for privileged group"""

        # observation terms
        thigh_contact = ObsTerm(
            func=mdp.is_contact,
            params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names=["FL_thigh", "FR_thigh","RL_thigh", "RR_thigh"], preserve_order=True), "threshold": 1.0}
        )
        actuator_gains = ObsTerm(
             func=mdp.actuator_gains,
             params={"asset_cfg": SceneEntityCfg("robot", joint_names=_SYMMETRY_JOINT_NAMES)},
        )
        com_offsets = ObsTerm(
             func=mdp.com_offset,
             params={"asset_cfg": SceneEntityCfg("robot", body_names="base"),
                     "event_name": "base_com"}
        )
        base_mass = ObsTerm(
             func=mdp.link_mass,
             params={"asset_cfg": SceneEntityCfg("robot", body_names="base")}
        )
        foot_restitution = ObsTerm(
             func=mdp.foot_restitution,
             params={"event_name": "physics_material"}
        )
        foot_friction = ObsTerm(
            func=mdp.foot_friction,
            params={"event_name": "physics_material"}
        )

        base_lin_vel = ObsTerm(
             func=mdp.base_lin_vel
        )
        base_ang_vel = ObsTerm(
            func=mdp.base_ang_vel, 
            noise=Unoise(n_min=-0.2, n_max=0.2)
        )
        projected_gravity = ObsTerm(
            func=mdp.projected_gravity,
        )
        velocity_commands = ObsTerm(
            func=mdp.generated_commands, 
            params={"command_name": "base_velocity"}
        )
        joint_pos = ObsTerm(
            func=mdp.joint_pos_rel, 
            params={"asset_cfg": SceneEntityCfg("robot", joint_names=_SYMMETRY_JOINT_NAMES)},
        )
        joint_vel = ObsTerm(
            func=mdp.joint_vel_rel, 
            params={"asset_cfg": SceneEntityCfg("robot", joint_names=_SYMMETRY_JOINT_NAMES)},
        )
        last_action = ObsTerm(
             func=mdp.last_action
        )
        terrain_height = ObsTerm(
             func=mdp.height_scan,
             params={"sensor_cfg": SceneEntityCfg("terrain_height_scanner")}
        )


        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    
    # observation groups
    proprio: PropriceptionCfg = PropriceptionCfg()
    commands: CommandObsCfg = CommandObsCfg()
    target: TargetCfg = TargetCfg()
    privilege: PrivilegCfg = PrivilegCfg()


@configclass
class EventsCfg:
    """Configuration for events."""

    # startup
    physics_material = EventTerm(
        func=mdp.randomize_shared_material,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names=".*foot"),
            "static_friction_range": (0.4, 1.2),
            "dynamic_friction_range": (0.3, 1.0),
            "restitution_range": (0.0, 0.1),
            "num_buckets": 64,
            "make_consistent": True,
        },
    )


    base_com = EventTerm(
        func=mdp.randomize_rigid_body_com,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names="base"),
            "com_range": {"x": (-0.05, 0.05), "y": (-0.05, 0.05), "z": (-0.01, 0.01)},
        },
    )

    base_mass = EventTerm(
        func=mdp.randomize_rigid_body_mass,
        mode="startup",
        params={
        "asset_cfg": SceneEntityCfg("robot", body_names="base"),
        "mass_distribution_params": (0.9, 1.1),
        "operation": "scale",
        "distribution": "log_uniform"
        }
    )

    # reset
    base_external_force_torque = EventTerm(
        func=mdp.apply_external_force_torque,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot", body_names="base"),
            "force_range": (0.0, 0.0),
            "torque_range": (-0.0, 0.0),
        },
    )

    reset_base = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "pose_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5), "yaw": (-3.14, 3.14)},
            "velocity_range": {
                "x": (-0.5, 0.5),
                "y": (-0.5, 0.5),
                "z": (-0.5, 0.5),
                "roll": (-0.5, 0.5),
                "pitch": (-0.5, 0.5),
                "yaw": (-0.5, 0.5),
            },
        },
    )

    reset_robot_joints = EventTerm(
        func=mdp.reset_joints_by_scale,
        mode="reset",
        params={
            "position_range": (0.5, 1.5),
            "velocity_range": (0.0, 0.0),
        },
    )

    # interval
    push_robot = EventTerm(
        func=mdp.push_by_setting_velocity,
        mode="interval",
        interval_range_s=(10.0, 15.0),
        params={"velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)}},
    )


@configclass
class RewardsCfg:
    """Reward terms for the MDP."""

    # -- task
    track_lin_vel_xy_exp = RewTerm(
        func=mdp.track_lin_vel_xy_exp, 
        weight=1.0, 
        params={"command_name": "base_velocity", 
                "std": math.sqrt(0.15)}
    )
    track_ang_vel_z_exp = RewTerm(
        func=mdp.track_ang_vel_z_exp, 
        weight=0.5, 
        params={"command_name": "base_velocity", 
                "std": math.sqrt(0.15)}
    )
    base_height_stance_exp = RewTerm(
        func=mdp.stance_base_height_orientation_exp,
        weight=1.0,
        params={"target_height": _GO2_STANDING_HEIGHT,
                "sigma_h": 0.1,
                "sigma_o": 0.1,
                "sensor_cfg": SceneEntityCfg("terrain_height_scanner")
        }
    )
    # -- auxilary rewards
    feet_air_time = RewTerm(
        func=mdp.feet_air_time,
        weight=0.5,
        params={
            "sensor_cfg": SceneEntityCfg("contact_forces", body_names=".*foot"),
            "command_name": "base_velocity",
            "threshold": 0.5,
        },
    )
    # -- penalties
    base_height_l2 = RewTerm(
        func=mdp.base_height_l2,
        weight=-5.0,
        params={"target_height": _GO2_STANDING_HEIGHT}
    )
    lin_vel_z_l2 = RewTerm(
        func=mdp.lin_vel_z_l2, 
        weight=-1.0
    )
    ang_vel_xy_l2 = RewTerm(
        func=mdp.ang_vel_xy_l2, 
        weight=-0.05
    )
    flat_orientation_l2 = RewTerm(
        func=mdp.flat_orientation_l2, 
        weight=-0.2
    )
    undesired_contacts = RewTerm(
        func=mdp.undesired_contacts,
        weight=-1.0,
        params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names=[".*THIGH", ".*CALF"]), "threshold": 1.0},
    )
    feet_stumble = RewTerm(
        func=mdp.feet_stumble,
        weight=-0.1,
        params={
            "sensor_cfg": SceneEntityCfg("contact_forces", body_names=".*foot")
        }
    )
    hip_abad_pos = RewTerm(
            func=mdp.joint_deviation_l2,
            weight=-1.0,
            params={
                "asset_cfg": SceneEntityCfg("robot",joint_names=".*_hip_joint"),
            },
        )
    dof_torques_l2 = RewTerm(
        func=mdp.joint_torques_l2, 
        weight=-1.0e-6
    )
    dof_acc_l2 = RewTerm(
        func=mdp.joint_acc_l2, 
        weight=-5.0e-7
    )
    mechanical_joint_power = RewTerm(
            func=mdp.joint_power,
            weight=-1.0e-6
    )
    action_rate_l2 = RewTerm(
        func=mdp.action_rate_l2, 
        weight=-0.01
    )
    action_smooth_l2 = RewTerm(
        func=mdp.action_smoothness_l2, 
        weight=-4.0e-3
    )
    


@configclass
class TerminationsCfg:
    """Termination terms for the MDP."""

    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    base_contact = DoneTerm(
        func=mdp.illegal_contact,
        params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names="base"), "threshold": 1.0},
    )


@configclass
class CurriculumCfg:
    """Curriculum terms for the MDP."""

    terrain_levels = CurrTerm(
        func=mdp.terrain_levels_vel
    )
    #TODO:add success rate adaptive curriculum


##
# Environment configuration
##


@configclass
class UnitreeGo2ParkourEnvCfg(ManagerBasedRLEnvCfg):
    """Configuration for the Unitree Go2 velocity-tracking environment on parkour terrain."""
    
    # Simulation settings
    sim: SimulationCfg = SimulationCfg(physics=RoughPhysicsCfg())
    # Scene settings
    scene: ParkourSceneCfg = ParkourSceneCfg(num_envs=4096, env_spacing=2.5)
    # Basic settings
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    commands: CommandsCfg = CommandsCfg()
    # MDP settings
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventsCfg = EventsCfg()
    curriculum: CurriculumCfg = CurriculumCfg()

    def __post_init__(self):
        """Post initialization."""
        # general settings
        self.decimation = 4
        self.episode_length_s = 20.0
        # simulation settings
        self.sim.dt = 0.005
        self.sim.render_interval = self.decimation
        self.sim.physics_material = self.scene.terrain.physics_material
        # update sensor update periods
        # we tick all the sensors based on the smallest update period (physics update period)
        if self.scene.terrain_height_scanner is not None:
            self.scene.terrain_height_scanner.update_period = self.decimation * self.sim.dt
        if self.scene.body_height_scanner is not None:
                self.scene.body_height_scanner.update_period = self.decimation * self.sim.dt
        if self.scene.fl_height_scanner is not None:
                self.scene.fl_height_scanner.update_period = self.decimation * self.sim.dt
        if self.scene.fr_height_scanner is not None:
                self.scene.fr_height_scanner.update_period = self.decimation * self.sim.dt
        if self.scene.rl_height_scanner is not None:
                self.scene.rl_height_scanner.update_period = self.decimation * self.sim.dt
        if self.scene.rr_height_scanner is not None:
                self.scene.rr_height_scanner.update_period = self.decimation * self.sim.dt
        if self.scene.contact_forces is not None:
            self.scene.contact_forces.update_period = self.sim.dt
        if self.scene.front_camera is not None:
             self.scene.front_camera.update_period = 5*self.decimation * self.sim.dt

        # check if terrain levels curriculum is enabled - if so, enable curriculum for terrain generator
        # this generates terrains with increasing difficulty and is useful for training
        if getattr(self.curriculum, "terrain_levels", None) is not None:
            if self.scene.terrain.terrain_generator is not None:
                self.scene.terrain.terrain_generator.curriculum = True
        else:
            if self.scene.terrain.terrain_generator is not None:
                self.scene.terrain.terrain_generator.curriculum = False

        # simulation
        # execute the DC motor actuators through the backend-native path
        self.sim.use_newton_actuators = True
        # scene
        self.scene.terrain_height_scanner.prim_path = "{ENV_REGEX_NS}/Robot/base"
        # scale down the terrains because the robot is small
        terrains = self.scene.terrain.terrain_generator.sub_terrains
        terrains["random_rough"].noise_range = (0.01, 0.06)
        terrains["random_rough"].noise_step = 0.01
        # actions
        self.actions.joint_pos.scale = 0.25
        # rewards
        self.rewards.feet_air_time.params["sensor_cfg"].body_names = ".*_foot"
        self.rewards.feet_air_time.weight = 0.01
        self.rewards.undesired_contacts = None
        self.rewards.dof_torques_l2.weight = -0.0002
        self.rewards.track_lin_vel_xy_exp.weight = 1.5
        self.rewards.track_ang_vel_z_exp.weight = 0.75
        self.rewards.dof_acc_l2.weight = -2.5e-7
        # base_height_l2: rough terrain, adjust target height using the height-scanner rays.
        self.rewards.base_height_l2.weight = -30.0
        self.rewards.base_height_l2.params["sensor_cfg"] = SceneEntityCfg("terrain_height_scanner")
        # action_rate_l2: halved from the shared default of -0.01. The stronger penalty locked
        # one hind foot into a low-amplitude, dragging gait on flat terrain with Newton.
        self.rewards.action_rate_l2.weight = -0.005
        # terminations
        self.terminations.base_contact.params["sensor_cfg"].body_names = "base"


        # Camera visualization
        # from isaaclab_visualizers.newton import NewtonGLVisualizerCfg
        # from isaaclab_visualizers.kit import KitVisualizerCfg

        # self.sim.visualizer_cfgs = [
        #     NewtonGLVisualizerCfg(
        #         streaming_view=True,
        #         streaming_sensor_prim_path=(
        #             "/World/envs/env_[^/]+/Robot/base/front_camera"
        #         ),
        #         streaming_envs=4,
        #         streaming_gt_types=["rgb"],
        #         streaming_depth_min=0.1,
        #         streaming_depth_max=5.0,
        #     ),
        #     KitVisualizerCfg(
        #         streaming_view=True,
        #         streaming_sensor_prim_path=(
        #             "/World/envs/env_[^/]+/Robot/base/front_camera"
        #         ),
        #         streaming_envs=4,
        #         streaming_gt_types=["rgb"],
        #         streaming_depth_min=0.1,
        #         streaming_depth_max=5.0,
        #     )
        # ]

    def play_mode(self):
        """Play-mode overrides shared by the velocity-tracking environments."""
        super().play_mode()
        # spawn the robot randomly in the grid (instead of their terrain levels)
        self.scene.terrain.max_init_terrain_level = None
        # reduce the number of terrains to save memory
        if self.scene.terrain.terrain_generator is not None:
            self.scene.terrain.terrain_generator.num_rows = 5
            self.scene.terrain.terrain_generator.num_cols = 5
            self.scene.terrain.terrain_generator.curriculum = False
        # remove random pushing events
        self.events.base_external_force_torque = None
        self.events.push_robot = None
