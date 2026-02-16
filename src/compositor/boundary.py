"""
boundary.py — Property boundary rendering on a separate transparent layer.

Draws the yellow property boundary with drop shadow onto its own Cairo surface.
The boundary is projected from ENU 3D coords to screen space.
"""
import cairo
import numpy as np
from .project import world_to_screen


def draw_boundary_layer(width, height, points_3d, view_matrix, proj_matrix, config,
                        viewport_width=2048, viewport_height=1536, enu_transform=None):
    """
    Render the property boundary onto a new transparent Cairo surface.

    Args:
        width, height: output surface dimensions
        points_3d: list of [e, n, z] ENU points from sidecar
        view_matrix, proj_matrix: 16-element column-major matrices
        config: dict with stroke_width, stroke_color, shadow_color
        viewport_width, viewport_height: viewport dimensions
        enu_transform: 4x4 numpy ENU→ECEF matrix (or None)

    Returns:
        cairo.ImageSurface with the boundary drawn on it (or None if < 2 points)
    """
    if not points_3d or len(points_3d) < 2:
        return None

    # Project all 3D points to 2D screen coordinates
    points_2d = []
    for p in points_3d:
        screen_p = world_to_screen(p, view_matrix, proj_matrix,
                                   viewport_width, viewport_height, enu_transform)
        if screen_p:
            print(f"DEBUG: boundary point {p} at {screen_p}")
            points_2d.append(screen_p)

    if len(points_2d) < 2:
        return None

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    def setup_path():
        ctx.new_path()
        ctx.move_to(points_2d[0][0], points_2d[0][1])
        for x, y in points_2d[1:]:
            ctx.line_to(x, y)
        ctx.close_path()

    stroke_width = config.get('stroke_width', 10)
    stroke_color = config.get('stroke_color', (1, 1, 0, 1))  # Yellow
    shadow_color = config.get('shadow_color', (0, 0, 0, 0.5))

    # 1. Drop shadow (offset slightly down-right for depth)
    shadow_offset = max(2, stroke_width * 0.3)
    ctx.save()
    ctx.translate(shadow_offset, shadow_offset)
    setup_path()
    ctx.set_source_rgba(*shadow_color)
    ctx.set_line_width(stroke_width * 1.2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    ctx.restore()

    # 2. Main yellow stroke
    setup_path()
    ctx.set_source_rgba(*stroke_color)
    ctx.set_line_width(stroke_width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve()

    # 3. Inner highlight (subtle 3D tube effect)
    ctx.set_source_rgba(1, 1, 1, 0.4)
    ctx.set_line_width(max(1, stroke_width * 0.15))
    ctx.stroke()

    return surface
