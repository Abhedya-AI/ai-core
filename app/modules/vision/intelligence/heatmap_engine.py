"""
intelligence/heatmap_engine.py — Activity & Movement Heatmap Engine.

Generates 2D spatial grid activity intensity maps from object bounding boxes
and centroid locations across camera views.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.entities.vision_safety_entities import HeatmapCell, HeatmapGrid

log = get_logger("vision.intelligence.heatmap")


class HeatmapEngine:
    """Engine aggregating worker & machinery movement into 2D spatial heatmaps."""

    def generate_grid_heatmap(
        self,
        zone_id: str,
        camera_id: str,
        centroids: list[tuple[float, float]],  # list of (norm_x 0-1, norm_y 0-1)
        grid_rows: int = 10,
        grid_cols: int = 10,
    ) -> HeatmapGrid:
        """Accumulate normalized detection centroids into a grid matrix."""
        counts = [[0 for _ in range(grid_cols)] for _ in range(grid_rows)]
        total = len(centroids)

        for nx, ny in centroids:
            col = min(int(nx * grid_cols), grid_cols - 1)
            row = min(int(ny * grid_rows), grid_rows - 1)
            if 0 <= col < grid_cols and 0 <= row < grid_rows:
                counts[row][col] += 1

        cells: list[HeatmapCell] = []
        for r in range(grid_rows):
            for c in range(grid_cols):
                cnt = counts[r][c]
                intensity = round(cnt / total, 3) if total > 0 else 0.0
                cells.append(HeatmapCell(x_cell=c, y_cell=r, intensity=intensity, detection_count=cnt))

        return HeatmapGrid(
            zone_id=zone_id,
            camera_id=camera_id,
            grid_rows=grid_rows,
            grid_cols=grid_cols,
            cells=cells,
        )
