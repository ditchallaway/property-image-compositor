"""
labels.py — Street label and acres text rendering on separate layers.

Each label gets its own transparent Cairo surface (for independent layer control).
Labels are projected from ENU 3D anchor points to screen space.
"""
import cairo
import numpy as np
from .project import world_to_screen, get_billboard_rotation


def draw_single_label(width, height, text, anchor_3d, view_matrix, proj_matrix,
                      camera_dir, config, viewport_width=2048, viewport_height=1536,
                      enu_transform=None):
    """
    Draw a single street label onto its own transparent surface.

    Args:
        width, height: output surface dimensions
        text: label text string
        anchor_3d: [e, n, z] ENU anchor point
        view_matrix, proj_matrix: matrices from sidecar
        camera_dir: camera direction dict from sidecar
        config: font configuration dict
        viewport_width, viewport_height: viewport dimensions
        enu_transform: ENU→ECEF transform matrix

    Returns:
        cairo.ImageSurface with the label drawn, or None if behind camera
    """
    pos = world_to_screen(anchor_3d, view_matrix, proj_matrix,
                          viewport_width, viewport_height, enu_transform)
    print(f"DEBUG: label '{text}' at {pos}")
    if not pos:
        return None

    screen_x, screen_y = pos

    # Skip if far outside viewport
    margin = 100
    if screen_x < -margin or screen_x > width + margin or \
       screen_y < -margin or screen_y > height + margin:
        return None

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    font_family = config.get('font_family', "sans-serif")
    font_size = config.get('font_size', 28)
    text_color = config.get('color', (1, 1, 1, 1))
    stroke_color = config.get('outline_color', (0, 0, 0, 1))

    ctx.select_font_face(font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(font_size)

    # Billboard rotation (face camera horizontally)
    rotation_deg = get_billboard_rotation(camera_dir)

    ctx.save()
    ctx.translate(screen_x, screen_y)
    ctx.rotate(np.radians(rotation_deg))

    # Center the text
    extents = ctx.text_extents(text)
    tx = -extents.width / 2
    ty = extents.height / 2

    # Outline
    ctx.move_to(tx, ty)
    ctx.text_path(text)
    ctx.set_source_rgba(*stroke_color)
    ctx.set_line_width(4)
    ctx.stroke_preserve()

    # Fill
    ctx.set_source_rgba(*text_color)
    ctx.fill()

    ctx.restore()

    return surface


def draw_street_label_layers(width, height, labels, view_matrix, proj_matrix,
                             camera_dir, config, viewport_width=2048,
                             viewport_height=1536, enu_transform=None):
    """
    Draw each street label on its own layer.

    Returns:
        list of (layer_name, cairo.ImageSurface) tuples
    """
    results = []

    for label in labels:
        text = label.get('text', '')
        if not text:
            continue
        anchor = label['anchor_3d']

        surface = draw_single_label(
            width, height, text, anchor,
            view_matrix, proj_matrix, camera_dir, config,
            viewport_width, viewport_height, enu_transform
        )
        if surface:
            results.append((text, surface))

    return results


def draw_acres_layer(width, height, centroid_3d, acres, view_matrix, proj_matrix,
                     config, viewport_width=2048, viewport_height=1536,
                     enu_transform=None):
    """
    Draw the acres label on its own transparent surface.

    Args:
        centroid_3d: [x, y, z] ECEF or ENU centroid
        acres: numeric acreage value or string
        config: font configuration dict

    Returns:
        cairo.ImageSurface with the acres text, or None if behind camera
    """
    formatted_acres = f"{acres:.1f}" if isinstance(acres, (int, float)) else str(acres)
    text = f"{formatted_acres} ACRES"

    pos = world_to_screen(centroid_3d, view_matrix, proj_matrix,
                          viewport_width, viewport_height, enu_transform)
    if not pos:
        return None

    screen_x, screen_y = pos

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    font_size = config.get('font_size', 64)
    font_family = config.get('font_family', "sans-serif")

    ctx.save()
    ctx.select_font_face(font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(font_size)

    # Center text
    extents = ctx.text_extents(text)
    tx = screen_x - (extents.width / 2)
    ty = screen_y + (extents.height / 2)

    # Shadow
    ctx.move_to(tx + 2, ty + 2)
    ctx.set_source_rgba(0, 0, 0, 0.7)
    ctx.show_text(text)

    # Yellow text
    ctx.move_to(tx, ty)
    ctx.set_source_rgba(1, 1, 0, 1)
    ctx.show_text(text)

    ctx.restore()

    return surface
