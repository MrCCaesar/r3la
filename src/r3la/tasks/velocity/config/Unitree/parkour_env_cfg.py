# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for the Unitree Go2 velocity-tracking environment on rough terrain."""

"""Base configuration for the velocity-tracking locomotion environments on rough terrain."""

import math
from dataclasses import MISSING
from os import replace

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
from isaaclab.sensors import ContactSensorCfg, patterns
from isaaclab.sim import SimulationCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.terrains.config.rough import ROUGH_TERRAINS_CFG
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR, ISAACLAB_NUCLEUS_DIR
from isaaclab.utils.noise import UniformNoiseCfg as Unoise

from isaaclab_tasks.utils import PresetCfg

##
# Task specific settings
##


import r3la.tasks.velocity.mdp as mdp
from r3la.labs.sensors import BaseYawHeightScannerCfg, HeldDepthCameraCfg
from r3la.labs.terrains import PARKOUR_TERRAINS_CFG
from r3la.labs.terrains.terrain_importer import ParkourTerrainImporter
# UNITREE_GO2_CFG.init_state.pos is (0, 0, 0.4) -- the asset's own authored standing height.
from isaaclab_assets.robots.unitree import UNITREE_GO2_CFG


_GO2_STANDING_HEIGHT = 0.4
_OBSERVATION_HISTORY_LENGTH = 5
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
        class_type=ParkourTerrainImporter,
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
    # Native capture clocks; target sensors are read only through the aligned bundle.
    front_camera = HeldDepthCameraCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base/front_camera",
        data_types=["rgb", "distance_to_image_plane"],
    )
    terrain_height_scanner = BaseYawHeightScannerCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base",
        heading_prim_path="{ENV_REGEX_NS}/Robot/base",
        update_period=0.02,
        pattern_cfg=patterns.GridPatternCfg(resolution=0.1, size=(1.6, 1.0), ordering="xy"),
    )
    body_height_scanner = BaseYawHeightScannerCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base",
        heading_prim_path="{ENV_REGEX_NS}/Robot/base",
        pattern_cfg=patterns.GridPatternCfg(resolution=0.05, size=(1.05, 0.6), ordering="xy"),
    )
    fl_height_scanner = BaseYawHeightScannerCfg(
        prim_path="{ENV_REGEX_NS}/Robot/FL_foot",
        heading_prim_path="{ENV_REGEX_NS}/Robot/base",
    )
    fr_height_scanner = BaseYawHeightScannerCfg(
        prim_path="{ENV_REGEX_NS}/Robot/FR_foot",
        heading_prim_path="{ENV_REGEX_NS}/Robot/base",
    )
    rl_height_scanner = BaseYawHeightScannerCfg(
        prim_path="{ENV_REGEX_NS}/Robot/RL_foot",
        heading_prim_path="{ENV_REGEX_NS}/Robot/base",
    )
    rr_height_scanner = BaseYawHeightScannerCfg(
        prim_path="{ENV_REGEX_NS}/Robot/RR_foot",
        heading_prim_path="{ENV_REGEX_NS}/Robot/base",
    )
    contact_forces = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/[^/]*", history_length=4, track_air_time=True,
        track_contact_points=True, filter_shape_prim_expr=["/World/ground/terrain/mesh"],
    )
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

    base_velocity = mdp.ParkourVelocityCommandCfg(resampling_time_range=(20.02, 20.02))


@configclass
class ActionsCfg:
    """Action specifications for the MDP."""

    joint_pos = mdp.JointPositionActionCfg(
            asset_name="robot", 
            joint_names=_SYMMETRY_JOINT_NAMES, 
            scale=0.5,
            preserve_order=True, 
            use_default_offset=True,
            clip=None,
        )


@configclass
class ObservationsCfg:
    """Observation specifications for the MDP."""

    @configclass
    class TargetCfg(ObsGroup):
        """Observations for reconstruction target."""

        body_height_scan = ObsTerm(func=mdp.low_rate_target, params={"key": "body_height_scan"})
        lf_height_scan = ObsTerm(func=mdp.low_rate_target, params={"key": "lf_height_scan"})
        rf_height_scan = ObsTerm(func=mdp.low_rate_target, params={"key": "rf_height_scan"})
        lh_height_scan = ObsTerm(func=mdp.low_rate_target, params={"key": "lh_height_scan"})
        rh_height_scan = ObsTerm(func=mdp.low_rate_target, params={"key": "rh_height_scan"})
        depth_image = ObsTerm(func=mdp.low_rate_target, params={"key": "depth_image"})

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
                            params={"asset_cfg": SceneEntityCfg(
                                "robot", joint_names=_SYMMETRY_JOINT_NAMES, preserve_order=True
                            )},
                            noise=Unoise(n_min=-0.01, n_max=0.01))
        joint_vel = ObsTerm(func=mdp.joint_vel_rel, 
                            params={"asset_cfg": SceneEntityCfg(
                                "robot", joint_names=_SYMMETRY_JOINT_NAMES, preserve_order=True
                            )},
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
        leg_contacts = ObsTerm(
            func=mdp.is_contact,
            params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names=["FL_thigh", "FR_thigh", "RL_thigh", "RR_thigh",
                        "FL_calf", "FR_calf", "RL_calf", "RR_calf"], preserve_order=True), "threshold": 1.0}
        )
        actuator_gains = ObsTerm(
             func=mdp.actuator_gains,
             params={"asset_cfg": SceneEntityCfg(
                 "robot", joint_names=_SYMMETRY_JOINT_NAMES, preserve_order=True
             )},
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
            params={"asset_cfg": SceneEntityCfg(
                "robot", joint_names=_SYMMETRY_JOINT_NAMES, preserve_order=True
            )},
        )
        joint_vel = ObsTerm(
            func=mdp.joint_vel_rel, 
            params={"asset_cfg": SceneEntityCfg(
                "robot", joint_names=_SYMMETRY_JOINT_NAMES, preserve_order=True
            )},
        )
        last_action = ObsTerm(
             func=mdp.last_action
        )
        terrain_height = ObsTerm(
             func=mdp.metric_height_scan,
             params={"sensor_cfg": SceneEntityCfg("terrain_height_scanner")}
        )


        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    
    @configclass
    class MetadataCfg(ObsGroup):
        """Per-row capture identity, timing and spatial masks; no noise/history."""

        episode_id = ObsTerm(func=mdp.sensor_metadata, params={"key": "episode_id"})
        low_rate_capture_time = ObsTerm(func=mdp.sensor_metadata, params={"key": "low_rate_capture_time"})
        low_rate_age = ObsTerm(func=mdp.sensor_metadata, params={"key": "low_rate_age"})
        low_rate_valid = ObsTerm(func=mdp.sensor_metadata, params={"key": "low_rate_valid"})
        depth_valid = ObsTerm(func=mdp.sensor_metadata, params={"key": "depth_valid"})
        body_height_valid = ObsTerm(func=mdp.sensor_metadata, params={"key": "body_height_valid"})
        lf_height_valid = ObsTerm(func=mdp.sensor_metadata, params={"key": "lf_height_valid"})
        rf_height_valid = ObsTerm(func=mdp.sensor_metadata, params={"key": "rf_height_valid"})
        lh_height_valid = ObsTerm(func=mdp.sensor_metadata, params={"key": "lh_height_valid"})
        rh_height_valid = ObsTerm(func=mdp.sensor_metadata, params={"key": "rh_height_valid"})
        base_height_valid = ObsTerm(func=mdp.amp_field, params={"key": "base_height_valid"})
        critic_height_valid = ObsTerm(func=mdp.sensor_metadata, params={"key": "critic_height_valid"})

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False

    @configclass
    class AmpCfg(ObsGroup):
        """Clean current physical fields for downstream AMP feature construction."""

        base_pos_w = ObsTerm(func=mdp.amp_field, params={"key": "base_pos_w"})
        base_quat_w = ObsTerm(func=mdp.amp_field, params={"key": "base_quat_w"})
        base_lin_vel_b = ObsTerm(func=mdp.amp_field, params={"key": "base_lin_vel_b"})
        base_ang_vel_b = ObsTerm(func=mdp.amp_field, params={"key": "base_ang_vel_b"})
        joint_pos = ObsTerm(func=mdp.amp_field, params={"key": "joint_pos", "asset_cfg": SceneEntityCfg("robot", joint_names=_SYMMETRY_JOINT_NAMES, preserve_order=True)})
        joint_vel = ObsTerm(func=mdp.amp_field, params={"key": "joint_vel", "asset_cfg": SceneEntityCfg("robot", joint_names=_SYMMETRY_JOINT_NAMES, preserve_order=True)})
        foot_pos_b = ObsTerm(func=mdp.amp_field, params={"key": "foot_pos_b", "asset_cfg": SceneEntityCfg("robot", body_names=["FL_foot", "FR_foot", "RL_foot", "RR_foot"], preserve_order=True)})
        base_height = ObsTerm(func=mdp.amp_field, params={"key": "base_height"})
        base_height_valid = ObsTerm(func=mdp.amp_field, params={"key": "base_height_valid"})

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False

    # observation groups
    proprio: PropriceptionCfg = PropriceptionCfg()
    commands: CommandObsCfg = CommandObsCfg()
    target: TargetCfg = TargetCfg()
    amp: AmpCfg = AmpCfg()
    metadata: MetadataCfg = MetadataCfg()
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
            "dynamic_friction_range": (0.4, 1.2),
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

    actuator_gains = EventTerm(
        func=mdp.randomize_actuator_gains,
        mode="startup",
        params={
            "asset_cfg": SceneEntityCfg("robot", joint_names=_SYMMETRY_JOINT_NAMES, preserve_order=True),
            "stiffness_distribution_params": (0.8, 1.2),
            "damping_distribution_params": (0.8, 1.2),
            "operation": "scale",
            "distribution": "uniform",
        },
    )

    reset_base = EventTerm(func=mdp.reset_parkour_state, mode="reset")

    # interval
    push_robot = None


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
                "contact_sensor_cfg": SceneEntityCfg("contact_forces", body_names=".*foot")
        }
    )
    # -- auxilary rewards
    feet_air_time = RewTerm(
        func=mdp.feet_air_time,
        weight=0.5,
        params={
            "sensor_cfg": SceneEntityCfg("contact_forces", body_names=".*foot"),
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
        params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names=[".*_thigh", ".*_calf"]), "threshold": 1.0},
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

    parkour_attempt = DoneTerm(func=mdp.ParkourAttemptState)
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    base_contact = DoneTerm(
        func=mdp.illegal_contact,
        params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names="base"), "threshold": 1.0},
    )


@configclass
class CurriculumCfg:
    """Curriculum terms for the MDP."""

    terrain_levels = CurrTerm(func=mdp.ParkourCurriculum)


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
        self.is_finite_horizon = False
        self.compute_final_obs = False
        # simulation settings
        self.sim.dt = 0.005
        self.sim.render_interval = self.decimation
        self.sim.physics_material = self.scene.terrain.physics_material
        # update sensor update periods
        # we tick all the sensors based on the smallest update period (physics update period)
        if self.scene.terrain_height_scanner is not None:
            self.scene.terrain_height_scanner.update_period = self.decimation * self.sim.dt
        if self.scene.body_height_scanner is not None:
                self.scene.body_height_scanner.update_period = 0.1
        if self.scene.fl_height_scanner is not None:
                self.scene.fl_height_scanner.update_period = 0.1
        if self.scene.fr_height_scanner is not None:
                self.scene.fr_height_scanner.update_period = 0.1
        if self.scene.rl_height_scanner is not None:
                self.scene.rl_height_scanner.update_period = 0.1
        if self.scene.rr_height_scanner is not None:
                self.scene.rr_height_scanner.update_period = 0.1
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
        #         streaming_gt_types=["depth"],
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
        """Use deterministic S34 evaluation defaults; configure explicit cases via evaluation.py."""
        from .evaluation import configure_parkour_evaluation

        super().play_mode()
        configure_parkour_evaluation(self)
