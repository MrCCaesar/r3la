"""Configuration for custom terrains."""

from isaaclab.terrains.terrain_generator_cfg import TerrainGeneratorCfg

from .terrain_generator import ParkourTerrainGenerator
from .trimesh import (
    ParkourGapTerrainCfg,
    ParkourRoughGridTerrainCfg,
    ParkourSideSlopeTerrainCfg,
    ParkourStairsTerrainCfg,
    ParkourSubTerrainCfg,
    ParkourTiltedStairsTerrainCfg,
)

PARKOUR_BOX_TERRAINS_CFG = TerrainGeneratorCfg(
    class_type=ParkourTerrainGenerator,
    seed=0,
    size=(10.0, 10.0),
    num_rows=10,
    num_cols=20,
    border_width=20.0,
    use_cache=False,
    curriculum=True,
    sub_terrains={"box": ParkourSubTerrainCfg()},
)


# Approved six-family aggregate. Keep the implementation-era export as an alias.

PARKOUR_TERRAINS_CFG = PARKOUR_BOX_TERRAINS_CFG.copy()
PARKOUR_TERRAINS_CFG.sub_terrains = {
    "box": ParkourSubTerrainCfg(proportion=0.2),
    "gap": ParkourGapTerrainCfg(proportion=0.2),
    "stairs": ParkourStairsTerrainCfg(proportion=0.1),
    "tilted_stairs": ParkourTiltedStairsTerrainCfg(proportion=0.2, holes=True),
    "side_slope": ParkourSideSlopeTerrainCfg(proportion=0.2),
    "rough_grid": ParkourRoughGridTerrainCfg(proportion=0.1),
}

PARKOUR_IMPLEMENTED_TERRAINS_CFG = PARKOUR_TERRAINS_CFG
