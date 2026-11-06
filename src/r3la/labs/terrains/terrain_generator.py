"""Native terrain generation with cache-independent task layout capture."""

import numpy as np

from isaaclab.terrains import TerrainGenerator
from isaaclab.utils import clone

from .layouts import PlacedTerrainLayout, build_terrain_layout


class ParkourTerrainGenerator(TerrainGenerator):
    """Keep all native mesh sampling/cache behavior; capture matching task records."""

    def __init__(self, cfg, device="cpu"):
        self.task_regions = np.empty((cfg.num_rows, cfg.num_cols), dtype=object)
        super().__init__(cfg, device=device)
        if any(record is None for record in self.task_regions.flat):
            raise ValueError("parkour terrain: incomplete task region table")
        self.terrain_mesh.metadata["r3la_task_regions"] = self.task_regions

    def _get_terrain_mesh(self, difficulty, cfg):
        effective = clone(cfg)
        effective.seed = self.cfg.seed
        self._pending_layout = build_terrain_layout(difficulty, effective)
        return super()._get_terrain_mesh(difficulty, cfg)

    def _add_sub_terrain(self, mesh, origin, row, col, sub_terrain_cfg):
        super()._add_sub_terrain(mesh, origin, row, col, sub_terrain_cfg)
        transform = np.eye(4, dtype=np.float64)
        # Native per-tile centering cancels the +half-tile placement. Global
        # centering is applied once after all sub-terrains have been generated.
        transform[:2, 3] = (
            (row - self.cfg.num_rows / 2) * self.cfg.size[0],
            (col - self.cfg.num_cols / 2) * self.cfg.size[1],
        )
        transform.flags.writeable = False
        self.task_regions[row, col] = PlacedTerrainLayout(self._pending_layout, row, col, transform)
