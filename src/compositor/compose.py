import json
import argparse
import os
import cairo
import numpy as np
from .boundary import draw_boundary
from .labels import draw_street_labels, draw_acres_label

def compose_image(png_path, json_path, output_path, config_path=None):
    """
    Main entry point for composing the final property image.
    """
    print(f"Composing: {png_path}")
    
    # 1. Load Sidecar JSON
    with open(json_path, 'r') as f:
        sidecar = json.load(f)
    
    # Extract matrices and metadata
    # Schema alignment: viewport and matrices are top-level
    matrices = sidecar.get('matrices', {})
    view_matrix_raw = matrices.get('view')
    proj_matrix_raw = matrices.get('projection')
    
    viewport_data = sidecar.get('viewport', sidecar.get('metadata', {}).get('viewport', {}))
    viewport_width = viewport_data.get('width', 2048)
    viewport_height = viewport_data.get('height', 1536)
    
    # Camera direction for bilboarding
    camera_data = sidecar.get('camera', {}).get('local_enu', {})
    camera_dir = camera_data.get('direction', {'x': 0, 'y': 0, 'z': -1})
    
    # Check for ENU -> ECEF transformation requirements
    # If the view matrix is ECEF (large values) and points are ENU (small values), 
    # we need the ENU frame to transform them.
    enu_transform = None
    if 'enu_axes' in sidecar and 'origin' in sidecar:
        axes = sidecar['enu_axes']
        origin = sidecar['origin']
        # Build 4x4 matrix from column vectors (East, North, Up) and Origin
        enu_transform = np.array([
            [axes['east']['x'], axes['north']['x'], axes['up']['x'], origin['x']],
            [axes['east']['y'], axes['north']['y'], axes['up']['y'], origin['y']],
            [axes['east']['z'], axes['north']['z'], axes['up']['z'], origin['z']],
            [0, 0, 0, 1]
        ])
    
    # 2. Setup Cairo Surface from base PNG
    surface = cairo.ImageSurface.create_from_png(png_path)
    ctx = cairo.Context(surface)
    
    # 3. Load Config (or use defaults)
    config = {}
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # 4. Draw Boundary
    # Schema alignment: boundary_3d is top-level direct list
    boundary_points = sidecar.get('boundary_3d', [])
    boundary_config = config.get('boundary', {
        'stroke_width': 12,
        'stroke_color': (1, 1, 0, 1), # Yellow
        'shadow_color': (0, 0, 0, 0.6)
    })
    draw_boundary(ctx, boundary_points, view_matrix_raw, proj_matrix_raw, 
                  boundary_config, viewport_width, viewport_height, enu_transform)
    
    # 5. Draw Street Labels
    labels = sidecar.get('labels', [])
    street_config = config.get('street_labels', {
        'font_size': 32,
        'color': (1, 1, 1, 1),
        'outline_color': (0, 0, 0, 1)
    })
    draw_street_labels(ctx, labels, view_matrix_raw, proj_matrix_raw, 
                       camera_dir, street_config, viewport_width, viewport_height, enu_transform)
    
    # 6. Draw Acres Label
    # Fallback to origin_wgs84 if centroid_3d is missing
    meta = sidecar.get('metadata', {})
    acres = meta.get('acres', config.get('default_acres', 'N/A'))
    
    # PhotoAgent uses origin as the centroid
    centroid = sidecar.get('origin', [0,0,0])
    if isinstance(centroid, dict):
        centroid = [centroid['x'], centroid['y'], centroid['z']]
        
    acres_config = config.get('acres_label', {
        'font_size': 72,
        'color': (1, 1, 0, 1)
    })
    # For the centroid (which is ECEF if taking from sidecar.origin), 
    # we pass enu_transform=None to avoid double transformation
    draw_acres_label(ctx, centroid, acres, view_matrix_raw, proj_matrix_raw, 
                     acres_config, viewport_width, viewport_height, None)
    
    # 7. Finalize and Save
    surface.write_to_png(output_path)
    print(f"✅ Composition complete: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Property Image Compositor")
    parser.add_argument("--png", required=True, help="Path to raw input PNG")
    parser.add_argument("--json", required=True, help="Path to sidecar JSON")
    parser.add_argument("--output", required=True, help="Path to save composed PNG")
    parser.add_argument("--config", help="Path to style config JSON")
    
    args = parser.parse_args()
    compose_image(args.png, args.json, args.output, args.config)
