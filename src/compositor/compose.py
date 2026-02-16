"""
compose.py — Layer-based property image compositor.

Orchestrates the composition pipeline:
  1. Load raw screenshot PNG (background layer)
  2. Build reference grid layer (scaffolding, hidden in PSD)
  3. Render boundary layer (yellow boundary with drop shadow)
  4. Render per-label layers (one layer per street label)
  5. Render acres layer
  6. Output as layered .psd, flat .png, or both.

The PSD output is the fail-to-manual deliverable: a human can open it,
toggle the grid layer, adjust label positions, and export manually.
"""
import json
import argparse
import os
import cairo
import numpy as np
from .boundary import draw_boundary_layer
from .labels import draw_street_label_layers, draw_acres_layer
from .grid import draw_grid_layer


def _build_enu_transform(sidecar):
    """Build 4x4 ENU→ECEF matrix from sidecar data, or None."""
    if 'enu_axes' not in sidecar or 'origin' not in sidecar:
        return None
    axes = sidecar['enu_axes']
    origin = sidecar['origin']
    return np.array([
        [axes['east']['x'], axes['north']['x'], axes['up']['x'], origin['x']],
        [axes['east']['y'], axes['north']['y'], axes['up']['y'], origin['y']],
        [axes['east']['z'], axes['north']['z'], axes['up']['z'], origin['z']],
        [0, 0, 0, 1]
    ])


def compose_image(png_path, json_path, output_path, config_path=None,
                  output_format='png', stage=2):
    """
    Main entry point for composing the final property image.

    Args:
        png_path: path to raw screenshot PNG
        json_path: path to sidecar JSON
        output_path: path for output file (.png or .psd based on format)
        config_path: optional style config JSON
        output_format: 'png', 'psd', or 'both'
        stage: 1 (lines only) or 2 (full composition including text)
    """
    print(f"Composing: {png_path} → {output_format} (Stage {stage})")

    # 1. Load Sidecar JSON
    with open(json_path, 'r') as f:
        sidecar = json.load(f)

    matrices = sidecar.get('matrices', {})
    view_matrix_raw = matrices.get('view')
    proj_matrix_raw = matrices.get('projection')

    viewport_data = sidecar.get('viewport', {})
    viewport_w = viewport_data.get('width', 2048)
    viewport_h = viewport_data.get('height', 1536)

    camera_data = sidecar.get('camera', {}).get('local_enu', {})
    camera_dir = camera_data.get('direction', {'x': 0, 'y': 0, 'z': -1})

    enu_transform = _build_enu_transform(sidecar)

    # 2. Load Config (or use defaults)
    config = {}
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)

    # 3. Load Background Image
    bg_surface = cairo.ImageSurface.create_from_png(png_path)
    img_w = bg_surface.get_width()
    img_h = bg_surface.get_height()

    # ─── Build Layers ───

    layers = []

    # Layer 0: Background (raw screenshot)
    layers.append({
        "name": "Background",
        "surface": bg_surface,
        "visible": True
    })

    # Layer 1: Reference Grid (scaffolding — hidden by default)
    boundary_points = sidecar.get('boundary_3d', [])
    try:
        grid_surface = draw_grid_layer(
            img_w, img_h, boundary_points,
            view_matrix_raw, proj_matrix_raw, enu_transform,
            viewport_w, viewport_h
        )
        layers.append({
            "name": "Grid (Reference)",
            "surface": grid_surface,
            "visible": False
        })
    except Exception as e:
        print(f"⚠️  Grid layer failed: {e}")

    # Layer 2: Property Boundary
    boundary_config = config.get('boundary', {
        'stroke_width': 12,
        'stroke_color': (1, 1, 0, 1),  # Yellow (#f6f90a approximation)
        'shadow_color': (0, 0, 0, 0.6)
    })
    try:
        boundary_surface = draw_boundary_layer(
            img_w, img_h, boundary_points,
            view_matrix_raw, proj_matrix_raw, boundary_config,
            viewport_w, viewport_h, enu_transform
        )
        if boundary_surface:
            layers.append({
                "name": "Boundary",
                "surface": boundary_surface,
                "visible": True
            })
    except Exception as e:
        print(f"⚠️  Boundary layer failed: {e}")

    # Layers 3..N: Street Labels (one per label) - ONLY IN STAGE 2+
    if stage >= 2:
        labels = sidecar.get('labels', [])
        street_config = config.get('street_labels', {
            'font_size': 32,
            'color': (1, 1, 1, 1),
            'outline_color': (0, 0, 0, 1)
        })
        try:
            label_layers = draw_street_label_layers(
                img_w, img_h, labels,
                view_matrix_raw, proj_matrix_raw, camera_dir, street_config,
                viewport_w, viewport_h, enu_transform
            )
            for label_name, label_surface in label_layers:
                layers.append({
                    "name": f"Label: {label_name}",
                    "surface": label_surface,
                    "visible": True
                })
        except Exception as e:
            print(f"⚠️  Label layers failed: {e}")

        # Layer N+1: Acres - ONLY IN STAGE 2+
        meta = sidecar.get('metadata', {})
        acres = meta.get('acres', config.get('default_acres', 'N/A'))
        centroid = sidecar.get('origin', {'x': 0, 'y': 0, 'z': 0})
        if isinstance(centroid, dict):
            centroid = [centroid['x'], centroid['y'], centroid['z']]

        acres_config = config.get('acres_label', {
            'font_size': 72,
            'color': (1, 1, 0, 1)
        })
        try:
            acres_surface = draw_acres_layer(
                img_w, img_h, centroid, acres,
                view_matrix_raw, proj_matrix_raw, acres_config,
                viewport_w, viewport_h, None  # centroid is ECEF, no double-transform
            )
            if acres_surface:
                layers.append({
                    "name": f"{acres:.1f} ACRES" if isinstance(acres, (int, float)) else str(acres),
                    "surface": acres_surface,
                    "visible": True
                })
        except Exception as e:
            print(f"⚠️  Acres layer failed: {e}")

    # ─── Output ───

    if output_format in ('png', 'both'):
        _export_flat_png(layers, output_path if output_format == 'png'
                         else output_path.replace('.psd', '.png'))

    if output_format in ('psd', 'both'):
        psd_path = output_path if output_format == 'psd' \
                   else output_path.replace('.png', '.psd')
        try:
            from .psd_export import export_psd
            export_psd(layers, psd_path)
        except Exception as e:
            print(f"⚠️  PSD export failed ({type(e).__name__}): {e}")
            print("   Falling back to PNG-only output to ensure delivery.")
            
            # Clean up partial PSD if it was created
            if os.path.exists(psd_path):
                try:
                    os.remove(psd_path)
                    print(f"   Deleted partial file: {psd_path}")
                except OSError as cleanup_err:
                    print(f"   ⚠️ Could not delete partial PSD: {cleanup_err}")

            # Fallback to PNG
            _export_flat_png(layers, output_path.replace('.psd', '.png'))

    print(f"✅ Composition complete: {output_path} ({len(layers)} layers)")


def _export_flat_png(layers, output_path):
    """Flatten all visible layers onto the background and save as PNG."""
    if not layers:
        return

    bg = layers[0]["surface"]
    width = bg.get_width()
    height = bg.get_height()

    # Create composite surface
    composite = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(composite)

    for layer_def in layers:
        if not layer_def.get("visible", True):
            continue
        ctx.set_source_surface(layer_def["surface"], 0, 0)
        ctx.paint()

    composite.write_to_png(output_path)
    print(f"   PNG saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Property Image Compositor")
    parser.add_argument("--png", required=True, help="Path to raw input PNG")
    parser.add_argument("--json", required=True, help="Path to sidecar JSON")
    parser.add_argument("--output", required=True, help="Path to save output")
    parser.add_argument("--config", help="Path to style config JSON")
    parser.add_argument("--format", dest="output_format", default="png",
                        choices=["png", "psd", "both"],
                        help="Output format: png, psd, or both")
    parser.add_argument("--stage", type=int, default=2,
                        help="Rendering stage: 1=lines only, 2=full (default: 2)")

    args = parser.parse_args()
    compose_image(args.png, args.json, args.output, args.config, args.output_format, args.stage)
