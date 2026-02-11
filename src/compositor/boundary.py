import cairo
import numpy as np
from .project import world_to_screen

def draw_boundary(ctx, points_3d, view_matrix, proj_matrix, config, viewport_width=2048, viewport_height=1536, enu_transform=None):
    """
    Draws a styled property boundary on a Cairo context.
    """
    if not points_3d or len(points_3d) < 2:
        return

    # Project all 3D points to 2D screen coordinates
    points_2d = []
    for p in points_3d:
        screen_p = world_to_screen(p, view_matrix, proj_matrix, viewport_width, viewport_height, enu_transform)
        if screen_p:
            points_2d.append(screen_p)
        else:
            # Handle points behind camera (for simplicity, we stop the line segment)
            pass

    if len(points_2d) < 2:
        return

    # Helper to draw a path
    def setup_path():
        ctx.new_path()
        ctx.move_to(points_2d[0][0], points_2d[0][1])
        for x, y in points_2d[1:]:
            ctx.line_to(x, y)
        ctx.close_path()

    stroke_width = config.get('stroke_width', 10)
    stroke_color = config.get('stroke_color', (1, 1, 0)) # Yellow default
    shadow_color = config.get('shadow_color', (0, 0, 0, 0.5)) # Black transparent

    # 1. Base Thick Stroke (The "Tube")
    setup_path()
    ctx.set_source_rgba(*stroke_color)
    ctx.set_line_width(stroke_width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve()

    # 2. Inner Shadow/Depth Effect
    # We thin the stroke and darken it slightly to create a tubular look
    ctx.set_source_rgba(*shadow_color)
    ctx.set_line_width(stroke_width * 0.4)
    ctx.stroke_preserve()

    # 3. Highlight/Center Line
    # A very thin bright line on top
    ctx.set_source_rgba(1, 1, 1, 0.6) # White highlight
    ctx.set_line_width(stroke_width * 0.1)
    ctx.stroke()
