from __future__ import annotations
import numpy as np
from app.core.logging import get_logger

log = get_logger(__name__)

class GridPropagationEngine:
    """Grid-based hazard propagation using 2D numpy arrays."""
    
    def __init__(self, grid_resolution_meters: float = 5.0) -> None:
        self._resolution = grid_resolution_meters
    
    def build_grid(self, zones: list[dict]) -> np.ndarray:
        """Create 2D numpy grid from zone bounding boxes."""
        if not zones:
            return np.zeros((10, 10), dtype=np.float32)
            
        min_x = min(z.get("x_min", 0.0) for z in zones)
        max_x = max(z.get("x_max", 0.0) for z in zones)
        min_y = min(z.get("y_min", 0.0) for z in zones)
        max_y = max(z.get("y_max", 0.0) for z in zones)
        
        width = max(max_x - min_x, self._resolution)
        height = max(max_y - min_y, self._resolution)
        
        cols = max(1, int(width / self._resolution))
        rows = max(1, int(height / self._resolution))
        
        return np.zeros((rows, cols), dtype=np.float32)
    
    def propagate_on_grid(
        self, grid: np.ndarray, source_cells: list[tuple[int, int]],
        intensity: float, steps: int, decay: float = 0.95
    ) -> np.ndarray:
        """BFS-like grid spread. Each step reduces intensity by decay."""
        new_grid = grid.copy()
        for r, c in source_cells:
            if 0 <= r < new_grid.shape[0] and 0 <= c < new_grid.shape[1]:
                new_grid[r, c] = intensity
                
        for _ in range(steps):
            up = np.roll(new_grid, shift=-1, axis=0)
            up[-1, :] = 0
            down = np.roll(new_grid, shift=1, axis=0)
            down[0, :] = 0
            left = np.roll(new_grid, shift=-1, axis=1)
            left[:, -1] = 0
            right = np.roll(new_grid, shift=1, axis=1)
            right[:, 0] = 0
            
            neighbors_max = np.maximum.reduce([up, down, left, right])
            new_grid = np.maximum(new_grid, neighbors_max * decay)
            
        return new_grid
    
    def grid_to_node_mapping(
        self, grid: np.ndarray, nodes: list[dict]
    ) -> dict[str, tuple[int, int]]:
        """Map node_id to (row, col) in grid using node coordinates."""
        mapping = {}
        rows, cols = grid.shape
        for node in nodes:
            node_id = node.get("node_id")
            if not node_id:
                continue
            
            x = node.get("x", 0.0)
            y = node.get("y", 0.0)
            
            c = int(x / self._resolution)
            r = int(y / self._resolution)
            
            mapping[node_id] = (min(max(0, r), rows - 1), min(max(0, c), cols - 1))
            
        return mapping
    
    def get_intensity_at_node(
        self, grid: np.ndarray, node_id: str, mapping: dict[str, tuple[int, int]]
    ) -> float:
        """Look up grid value at node's mapped cell."""
        if node_id in mapping:
            r, c = mapping[node_id]
            if 0 <= r < grid.shape[0] and 0 <= c < grid.shape[1]:
                return float(grid[r, c])
        return 0.0
    
    def export_grid_to_dict(
        self, grid: np.ndarray, mapping: dict[str, tuple[int, int]]
    ) -> dict[str, float]:
        """Returns node_id -> intensity for all mapped nodes."""
        result = {}
        for node_id, (r, c) in mapping.items():
            if 0 <= r < grid.shape[0] and 0 <= c < grid.shape[1]:
                result[node_id] = float(grid[r, c])
            else:
                result[node_id] = 0.0
        return result
