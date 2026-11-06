"""Native mesh importer exposing validated local task data on the simulation device."""

import numpy as np
import torch

from isaaclab.terrains import TerrainImporter

from .layouts import PlacedTerrainLayout, RoughGridGeometry, SideSlopeGeometry, StairGeometry


class ParkourTerrainImporter(TerrainImporter):
    """Keep local predicates and a rigid tile transform, never infer spawn from origin."""

    def import_mesh(self, name, mesh):
        table = mesh.metadata.get("r3la_task_regions")
        generator = self.cfg.terrain_generator
        expected = (generator.num_rows, generator.num_cols)
        if not isinstance(table, np.ndarray) or table.shape != expected:
            raise ValueError("parkour terrain: missing or inconsistent task region metadata")
        for (row, col), record in np.ndenumerate(table):
            if not isinstance(record, PlacedTerrainLayout) or (record.level, record.column) != (row, col):
                raise ValueError("parkour terrain: invalid task region placement")
        self.task_regions = table
        self._prepare_task_tensors(table)
        super().import_mesh(name, mesh)

    def _prepare_task_tensors(self, table):
        def tensor(values, dtype=torch.float32):
            return torch.tensor(np.array(values), device=self.device, dtype=dtype)

        def field(accessor, dtype=torch.float32):
            return tensor([[accessor(record) for record in line] for line in table], dtype)

        self.task_tile_to_world = field(lambda r: r.tile_to_world)
        self.task_spawn_pos = field(lambda r: r.layout.spawn_pos @ r.tile_to_world[:3, :3].T + r.tile_to_world[:3, 3])
        self.task_spawn_yaw = field(
            lambda r: r.layout.spawn_yaw + np.arctan2(r.tile_to_world[1, 0], r.tile_to_world[0, 0])
        )
        self.task_legal_xy = field(lambda r: r.layout.legal_xy)
        self.task_completion_xy = field(lambda r: r.layout.completion_xy)
        self.task_support_xy = field(lambda r: r.layout.support_surface.xy_bounds)
        self.task_support_normal = field(lambda r: r.layout.support_surface.normal)
        self.task_support_offset = field(lambda r: r.layout.support_surface.offset)
        self.task_support_normal_w = field(lambda r: r.tile_to_world[:3, :3] @ r.layout.support_surface.normal)
        self.task_support_offset_w = field(
            lambda r: (
                r.layout.support_surface.offset
                - np.dot(r.tile_to_world[:3, :3] @ r.layout.support_surface.normal, r.tile_to_world[:3, 3])
            )
        )
        self.task_difficulty = field(lambda r: r.layout.difficulty)
        families = ("box", "gap", "stairs", "tilted_stairs", "side_slope", "rough_grid")
        self.task_family_id = field(lambda r: families.index(r.layout.family), torch.int64)
        self.task_mirror_sign = field(lambda r: r.layout.mirror_sign, torch.int64)
        self.task_seed = field(lambda r: r.layout.seed, torch.int64)
        self.task_schema_version = field(lambda r: r.layout.schema_version, torch.int64)
        # Strings remain generation-time identities; stable integer indices refer to them at runtime.
        self.task_canonical_ids = tuple(dict.fromkeys(r.layout.canonical_id for r in table.flat))
        canonical_indices = {identity: i for i, identity in enumerate(self.task_canonical_ids)}
        self.task_canonical_id = field(lambda r: canonical_indices[r.layout.canonical_id], torch.int64)
        self.task_gate_count = field(lambda r: len(r.layout.gates), torch.int64)
        max_gates = max(len(r.layout.gates) for r in table.flat)
        gates = np.zeros((*table.shape, max_gates, 3), dtype=np.float32)
        for index, record in np.ndenumerate(table):
            for gate_id, gate in enumerate(record.layout.gates):
                gates[*index, gate_id] = (gate.x, *gate.y_bounds)
        self.task_gates = tensor(gates)
        self.task_gate_valid = torch.arange(max_gates, device=self.device) < self.task_gate_count[..., None]

        self.task_tread_count = field(
            lambda r: r.layout.geometry.count if isinstance(r.layout.geometry, StairGeometry) else 0, torch.int64
        )
        max_treads = int(self.task_tread_count.max().item())
        tread_bounds = np.zeros((*table.shape, max_treads, 2, 2), dtype=np.float32)
        tread_planes = np.zeros((*table.shape, max_treads, 4), dtype=np.float32)
        for index, record in np.ndenumerate(table):
            geometry = record.layout.geometry
            if isinstance(geometry, StairGeometry):
                tread_bounds[*index, : geometry.count] = geometry.tread_bounds
                tread_planes[*index, : geometry.count] = geometry.tread_planes
        self.task_tread_bounds = tensor(tread_bounds)
        self.task_tread_planes = tensor(tread_planes)
        self.task_tread_valid = torch.arange(max_treads, device=self.device) < self.task_tread_count[..., None]

        self.task_slope_valid = field(lambda r: isinstance(r.layout.geometry, SideSlopeGeometry), torch.bool)
        self.task_slope_break_x = field(
            lambda r: r.layout.geometry.break_x if isinstance(r.layout.geometry, SideSlopeGeometry) else np.zeros(2)
        )
        self.task_slope_center_y = field(
            lambda r: r.layout.geometry.center_y if isinstance(r.layout.geometry, SideSlopeGeometry) else 0.0
        )
        self.task_slope_coefficient = field(
            lambda r: r.layout.geometry.slope if isinstance(r.layout.geometry, SideSlopeGeometry) else 0.0
        )

        self.task_grid_valid = field(lambda r: isinstance(r.layout.geometry, RoughGridGeometry), torch.bool)
        self.task_grid_x_edges = field(
            lambda r: r.layout.geometry.x_edges if isinstance(r.layout.geometry, RoughGridGeometry) else np.zeros(11)
        )
        self.task_grid_y_edges = field(
            lambda r: r.layout.geometry.y_edges if isinstance(r.layout.geometry, RoughGridGeometry) else np.zeros(11)
        )
        self.task_grid_heights = field(
            lambda r: (
                r.layout.geometry.heights if isinstance(r.layout.geometry, RoughGridGeometry) else np.zeros((10, 10))
            )
        )
