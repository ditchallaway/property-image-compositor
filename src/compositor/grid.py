"""
grid.py — Euclidean Reference Grid

Projects a regular grid of equal squares from ENU space onto the image.
The grid acts as scaffolding: a coordinate system for placing labels/boundary
in correct perspective. Remove the grid layer from the final PSD before delivery.

Math:
  ENU point (e, n, ground_z) → enu_transform → ECEF → view → proj → screen
"""
import math
import cairo
import numpy as np
from .project import world_to_screen


def _nice_round(value):
    """Round to a 'nice' number (1, 2, 5, 10, 20, 25, 50, 100, ...)."""
    if value <= 0:
        return 10.0
    exponent = math.floor(math.log10(value))
    fraction = value / (10 ** exponent)
    if fraction <= 1.5:
        nice = 1
    elif fraction <= 3.5:
        nice = 2
    elif fraction <= 7.5:
        nice = 5
    else:
        nice = 10
    return nice * (10 ** exponent)


def compute_grid(boundary_3d, extend_factor=3.0, target_cells=15):
    """
    Compute a flat Euclidean grid in ENU space at the boundary's ground level.

    Args:
        boundary_3d: list of [e, n, z] ENU points from sidecar
        extend_factor: how far beyond the boundary bbox to extend the grid
        target_cells: approximate number of cells across the property

    Returns:
        dict with:
            ground_z: float — the Z level of the grid
            cell_size: float — size of each square in meters
            east_lines: list of [(e, n, z), ...] polylines running N-S
            north_lines: list of [(e, n, z), ...] polylines running E-W
    """
    if not boundary_3d or len(boundary_3d) < 2:
        return {"ground_z": 0, "cell_size": 10, "east_lines": [], "north_lines": []}

    pts = np.array(boundary_3d)
    east_vals = pts[:, 0]
    north_vals = pts[:, 1]

    # Ground level = mean Z of boundary (accounts for the ENU offset)
    ground_z = float(np.mean(pts[:, 2]))

    # Boundary bounding box
    e_min, e_max = float(east_vals.min()), float(east_vals.max())
    n_min, n_max = float(north_vals.min()), float(north_vals.max())
    bbox_size = max(e_max - e_min, n_max - n_min)

    # Cell size — round to a nice number
    cell_size = _nice_round(bbox_size / target_cells)
    if cell_size < 1:
        cell_size = 1.0

    # Grid center (center of boundary bbox)
    center_e = (e_min + e_max) / 2.0
    center_n = (n_min + n_max) / 2.0

    # Extent beyond boundary
    extent = bbox_size * extend_factor / 2.0

    # Snap grid origin to cell boundaries
    grid_e_min = math.floor((center_e - extent) / cell_size) * cell_size
    grid_e_max = math.ceil((center_e + extent) / cell_size) * cell_size
    grid_n_min = math.floor((center_n - extent) / cell_size) * cell_size
    grid_n_max = math.ceil((center_n + extent) / cell_size) * cell_size

    # East lines: vertical lines running N→S at each East step
    east_lines = []
    e = grid_e_min
    while e <= grid_e_max:
        line = [(e, grid_n_min, ground_z), (e, grid_n_max, ground_z)]
        east_lines.append(line)
        e += cell_size

    # North lines: horizontal lines running E→W at each North step
    north_lines = []
    n = grid_n_min
    while n <= grid_n_max:
        line = [(grid_e_min, n, ground_z), (grid_e_max, n, ground_z)]
        north_lines.append(line)
        n += cell_size

    return {
        "ground_z": ground_z,
        "cell_size": cell_size,
        "east_lines": east_lines,
        "north_lines": north_lines,
    }


def draw_grid_layer(width, height, boundary_3d, view_matrix, proj_matrix,
                    enu_transform, viewport_w, viewport_h,
                    line_color=(1, 1, 1, 0.25), line_width=1.0):
    """
    Render the reference grid onto a transparent Cairo surface.

    Args:
        width, height: output image dimensions
        boundary_3d: boundary points from sidecar (used to derive grid)
        view_matrix, proj_matrix: 16-element column-major matrices
        enu_transform: 4x4 numpy ENU→ECEF matrix (or None)
        viewport_w, viewport_h: viewport dimensions from sidecar
        line_color: RGBA tuple for grid lines
        line_width: width of grid lines in pixels

    Returns:
        cairo.ImageSurface with the grid drawn on it
    """
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    grid = compute_grid(boundary_3d)
    all_lines = grid["east_lines"] + grid["north_lines"]

    ctx.set_source_rgba(*line_color)
    ctx.set_line_width(line_width)
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)

    for line in all_lines:
        # Project endpoints
        p0 = world_to_screen(line[0], view_matrix, proj_matrix,
                             viewport_w, viewport_h, enu_transform)
        p1 = world_to_screen(line[1], view_matrix, proj_matrix,
                             viewport_w, viewport_h, enu_transform)

        if p0 is None or p1 is None:
            continue

        # Cull lines entirely outside viewport (with margin)
        margin = 200
        if (p0[0] < -margin and p1[0] < -margin) or \
           (p0[0] > width + margin and p1[0] > width + margin) or \
           (p0[1] < -margin and p1[1] < -margin) or \
           (p0[1] > height + margin and p1[1] > height + margin):
            continue

        ctx.move_to(p0[0], p0[1])
        ctx.line_to(p1[0], p1[1])

    ctx.stroke()

    return surface
