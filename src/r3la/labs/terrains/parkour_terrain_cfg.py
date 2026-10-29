"""Configuration for custom terrains."""

import isaaclab.terrains as terrain_gen
from isaaclab.terrains.terrain_generator_cfg import TerrainGeneratorCfg

PARKOUR_TERRAINS_CFG = TerrainGeneratorCfg(
    size=(8.0, 8.0),
    border_width=20.0,
    num_rows=10,
    num_cols=20,
    horizontal_scale=0.1,
    vertical_scale=0.005,
    slope_threshold=0.75,
    use_cache=False,
    sub_terrains={
        "rails": terrain_gen.MeshRailsTerrainCfg(
            proportion=0.2,
            rail_thickness_range=(0.3, 0.3),
            rail_height_range=(0.4, 0.6),
            platform_width=2.0,
        ),
        "gaps": terrain_gen.MeshGapTerrainCfg(
            proportion=0.2,
            gap_width_range=(0.3, 0.8),
            platform_width=2.0,
        ),
        "pits": terrain_gen.MeshPitTerrainCfg(
            proportion=0.2,
            pit_depth_range=(0.5, 0.7),
            platform_width=2.0,
            double_pit=True,
        ),
        "boxes": terrain_gen.MeshBoxTerrainCfg(
            proportion=0.2,
            box_height_range=(0.5, 1.0),
            platform_width=2.0,
            double_box=True,
        ),
        "flat": terrain_gen.MeshPlaneTerrainCfg(
            proportion=0.1
        ),
        "random_rough": terrain_gen.HfRandomUniformTerrainCfg(
            proportion=0.1, noise_range=(0.02, 0.10), noise_step=0.02, border_width=0.25
        ),
    },
)
"""Rough terrains configuration."""