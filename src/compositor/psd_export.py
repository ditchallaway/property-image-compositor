"""
psd_export.py — Assemble Cairo surfaces into a layered PSD file.

Uses pytoshop to create a Photoshop-compatible PSD with:
  - Background layer (the raw screenshot)
  - Grid layer (hidden scaffolding)
  - Boundary layer (yellow boundary with shadow)
  - Per-label layers (one layer per street label)
  - Acres layer

Each layer is a separate transparent surface, enabling manual editing.
"""
import numpy as np

try:
    import pytoshop
    from pytoshop import layers as psd_layers
    from pytoshop.enums import ColorMode, Compression
    HAS_PYTOSHOP = True
except ImportError:
    HAS_PYTOSHOP = False


def _cairo_surface_to_channels(surface):
    """
    Convert a Cairo ARGB32 surface to separate R, G, B, A numpy arrays.
    Cairo stores pixels as BGRA in native byte order (little-endian on x86).

    Returns:
        (R, G, B, A) tuple of uint8 numpy arrays, each shape (height, width)
    """
    surface.flush()
    width = surface.get_width()
    height = surface.get_height()
    stride = surface.get_stride()

    # Get raw buffer
    buf = surface.get_data()
    # Cairo ARGB32: each pixel is 4 bytes in BGRA order (on little-endian)
    arr = np.frombuffer(buf, dtype=np.uint8).copy()

    # Stride may include padding; reshape accounting for stride
    rows = []
    for y in range(height):
        row_start = y * stride
        row = arr[row_start:row_start + width * 4].reshape(width, 4)
        rows.append(row)
    pixels = np.stack(rows)  # shape: (height, width, 4)

    # Cairo native byte order on little-endian: B, G, R, A
    b_chan = pixels[:, :, 0]
    g_chan = pixels[:, :, 1]
    r_chan = pixels[:, :, 2]
    a_chan = pixels[:, :, 3]

    return r_chan, g_chan, b_chan, a_chan


def _make_layer(name, surface, visible=True):
    """Create a pytoshop LayerRecord from a Cairo surface."""
    r, g, b, a = _cairo_surface_to_channels(surface)
    height, width = r.shape

    # pytoshop ChannelImageData takes image= (2D numpy array)
    # Channel keys: -1 = transparency, 0 = red, 1 = green, 2 = blue
    layer = psd_layers.LayerRecord(
        name=name,
        top=0,
        left=0,
        bottom=height,
        right=width,
        opacity=255 if visible else 128,
        visible=visible,
        channels={
            -1: psd_layers.ChannelImageData(
                image=a, compression=Compression.raw
            ),
            0: psd_layers.ChannelImageData(
                image=r, compression=Compression.raw
            ),
            1: psd_layers.ChannelImageData(
                image=g, compression=Compression.raw
            ),
            2: psd_layers.ChannelImageData(
                image=b, compression=Compression.raw
            ),
        }
    )
    return layer


def export_psd(layer_defs, output_path):
    """
    Export a list of layer definitions to a PSD file.

    Args:
        layer_defs: list of dicts:
            [
                {"name": "Background", "surface": cairo_surface, "visible": True},
                {"name": "Grid (Reference)", "surface": grid_surface, "visible": False},
                ...
            ]
        output_path: path to write the .psd file

    Raises:
        ImportError: if pytoshop is not installed
    """
    if not HAS_PYTOSHOP:
        raise ImportError(
            "pytoshop is required for PSD export. "
            "Install with: pip install pytoshop"
        )

    if not layer_defs:
        raise ValueError("No layers provided for PSD export")

    # Use dimensions from the first layer
    first_surface = layer_defs[0]["surface"]
    width = first_surface.get_width()
    height = first_surface.get_height()

    # Create PSD file
    psd = pytoshop.PsdFile(
        num_channels=3,
        height=height,
        width=width,
        depth=8,
        color_mode=ColorMode.rgb,
    )

    # Add layers (pytoshop renders bottom layer first)
    for layer_def in layer_defs:
        layer = _make_layer(
            name=layer_def["name"],
            surface=layer_def["surface"],
            visible=layer_def.get("visible", True),
        )
        psd.layer_and_mask_info.layer_info.layer_records.append(layer)

    with open(output_path, 'wb') as f:
        psd.write(f)

    print(f"✅ PSD exported: {output_path} ({len(layer_defs)} layers)")
