import cairo
import numpy as np
from .project import world_to_screen, get_billboard_rotation

def draw_street_labels(ctx, labels, view_matrix, proj_matrix, camera_dir, config, viewport_width=2048, viewport_height=1536, enu_transform=None):
    """
    Draws billboard-style street labels at 3D anchor points.
    """
    font_family = config.get('font_family', "sans-serif")
    font_size = config.get('font_size', 28)
    text_color = config.get('color', (1, 1, 1)) # White
    stroke_color = config.get('outline_color', (0, 0, 0)) # Black outline
    
    ctx.select_font_face(font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(font_size)

    # Calculate billboards' shared rotation (facing camera horizontally)
    rotation_deg = get_billboard_rotation(camera_dir)

    for label in labels:
        text = label['text']
        anchor = label['anchor_3d']
        
        pos = world_to_screen(anchor, view_matrix, proj_matrix, viewport_width, viewport_height, enu_transform)
        if not pos:
            continue
            
        screen_x, screen_y = pos
        
        ctx.save()
        ctx.translate(screen_x, screen_y)
        ctx.rotate(np.radians(rotation_deg)) # Optional: Rotate to align with camera
        
        # Center the text
        extents = ctx.text_extents(text)
        tx = -extents.width / 2
        ty = extents.height / 2
        
        # Draw outline
        ctx.move_to(tx, ty)
        ctx.text_path(text)
        ctx.set_source_rgba(*stroke_color)
        ctx.set_line_width(4)
        ctx.stroke_preserve()
        
        # Draw fill
        ctx.set_source_rgba(*text_color)
        ctx.fill()
        
        ctx.restore()

def draw_acres_label(ctx, centroid_3d, acres, view_matrix, proj_matrix, config, viewport_width=2048, viewport_height=1536, enu_transform=None):
    """
    Draws the acre label centered on the property.
    Currently uses perspective billboard style.
    """
    # Format acres: rounded to 1 decimal place (e.g., "6.5") and uppercase
    # If integer, show no decimal? Standard logic: .1f or .2f
    formatted_acres = f"{acres:.1f}" if isinstance(acres, (int, float)) else str(acres)
    text = f"{formatted_acres} ACRES"
    pos = world_to_screen(centroid_3d, view_matrix, proj_matrix, viewport_width, viewport_height, enu_transform)
    if not pos:
        return
        
    screen_x, screen_y = pos
    font_size = config.get('font_size', 64)
    
    ctx.save()
    ctx.select_font_face(config.get('font_family', "sans-serif"), 
                         cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(font_size)
    
    # Center text
    extents = ctx.text_extents(text)
    tx = screen_x - (extents.width / 2)
    ty = screen_y + (extents.height / 2)
    
    # Draw shadow/outline
    ctx.move_to(tx + 2, ty + 2)
    ctx.set_source_rgba(0, 0, 0, 0.7)
    ctx.show_text(text)
    
    # Draw main text
    ctx.move_to(tx, ty)
    ctx.set_source_rgba(1, 1, 0, 1) # Yellow
    ctx.show_text(text)
    
    ctx.restore()
