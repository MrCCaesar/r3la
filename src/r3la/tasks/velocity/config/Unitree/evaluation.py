"""Deterministic fixed-family evaluation using the same task and native managers."""

import math

from isaaclab.managers import EventTermCfg

from r3la.tasks.velocity.mdp.events import set_evaluation_terrain


def configure_parkour_evaluation(cfg, family="box", level=0, velocity=1.0, mirror_sign=1, seed=0):
    """Apply approved S34 evaluation settings in place, returning the config.

    Family is one of the six training families; level is integer 0..9, velocity
    is finite [0,3] m/s, mirror_sign -1 is valid only for tilted stairs/side slope.
    Same seed/family/level yields canonical geometry shared by mirror pairs.
    Two environments by default; callers may set a safe explicit count afterwards.
    """
    from r3la.labs.terrains import PARKOUR_TERRAINS_CFG

    families = PARKOUR_TERRAINS_CFG.sub_terrains
    if family not in families or type(level) is not int or not 0 <= level <= 9:
        raise ValueError("Evaluation requires a supported family and integer level in [0,9]")
    if mirror_sign not in (-1, 1) or (mirror_sign == -1 and family not in ("tilted_stairs", "side_slope")):
        raise ValueError("Only tilted_stairs and side_slope support mirror_sign=-1")
    if not math.isfinite(velocity) or not 0 <= velocity <= 3:
        raise ValueError("Evaluation forward velocity must be finite and in [0,3] m/s")
    if type(seed) is not int or seed < 0:
        raise ValueError("Evaluation seed must be a nonnegative integer")
    cfg.seed = seed
    cfg.scene.num_envs = 2
    generator = PARKOUR_TERRAINS_CFG.copy()
    generator.num_cols = 1
    generator.seed = seed
    generator.curriculum = True  # retain native per-level difficulty strata, not random allocation
    generator.sub_terrains = {family: families[family].replace(proportion=1.0, mirror_sign=mirror_sign)}
    cfg.scene.terrain.terrain_generator = generator
    cfg.scene.terrain.max_init_terrain_level = level
    cfg.curriculum.terrain_levels = None
    cfg.commands.base_velocity.evaluation_velocity = velocity
    cfg.events.base_com = cfg.events.base_mass = cfg.events.actuator_gains = None
    cfg.events.physics_material.params["nominal"] = True
    cfg.events.reset_base.params["nominal"] = True
    cfg.events.evaluation_terrain = EventTermCfg(func=set_evaluation_terrain, mode="startup", params={"level": level})
    cfg.observations.privilege.com_offsets.params["event_name"] = None
    for group in vars(cfg.observations).values():
        if hasattr(group, "enable_corruption"):
            group.enable_corruption = False
            for term in vars(group).values():
                if hasattr(term, "noise"):
                    term.noise = None
    return cfg


def make_parkour_evaluation_cfg(family="box", level=0, velocity=1.0, mirror_sign=1, seed=0):
    """Create a native env config; selection contracts are in configure_parkour_evaluation."""
    from .parkour_env_cfg import UnitreeGo2ParkourEnvCfg

    return configure_parkour_evaluation(UnitreeGo2ParkourEnvCfg(), family, level, velocity, mirror_sign, seed)
