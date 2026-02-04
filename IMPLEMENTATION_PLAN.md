# Implementation Plan - Property Image Compositor

> **Service Context**: This compositor is the second component of the **Virtual Drone Photography for Real Estate** service. The first component, **Robotic Property Photographer**, generates raw renders. This component produces final delivery-ready images.

Fully automated Python service that consumes rendered PNGs and sidecar JSON to produce client-deliverable property images with styled boundary overlays and billboard street labels.

---

## User Review Required

> [!IMPORTANT]
> **Billboard Text Orientation (Street Labels Only)**: Street labels will rotate horizontally to face the camera but remain **perpendicular to the ground plane** (no vertical tilt). Text will not angle upward toward the camera - it stays flat like a road sign. This is simpler than full 3D billboard rotation.

> [!IMPORTANT]
> **Acres Text Uses Perspective Projection**: Unlike street labels, the acres text follows the property's ground plane with full 3D perspective. This requires calculating the property's major axis orientation and applying a perspective transform so text appears to "lay on" the property at the correct angle.

> [!IMPORTANT]
> **Styling Configuration**: Boundary stroke width, colors, shadows, and text fonts will be externalized to a config file for easy adjustment without code changes. Colors use standard RGB hex format (#RRGGBB) or RGBA tuples, not KML's AABBGGRR format.

---

## Proposed Changes

### Python Module: `compositor/`

A Python module that runs in n8n's external Python runner environment.

#### Core Components

**1. `compositor/project.py`** - 3D → 2D Projection
- Parse view/projection matrices from sidecar JSON (column-major format)
- Implement projection function: `world_to_screen(point_3d, view_matrix, proj_matrix, viewport)`
- Handle normalized device coordinates → pixel coordinates conversion

**2. `compositor/boundary.py`** - Property Boundary Overlay
- Parse `boundary_3d` from sidecar JSON
- Project each boundary point to 2D screen space
- Render polygon with multi-layer styling to achieve 3D tubular effect:
  - **Base stroke**: 8-10px yellow (#FFFF00)
  - **Inner shadow**: Dark gradient inside stroke for depth
  - **Outer glow** (optional): Subtle highlight for "lift" from terrain
- Configurable stroke width, colors, and shadow parameters

> [!TIP]
> **Visual Reference**: See `examples/` folder for before/after images showing the exact boundary effect style.

**3. `compositor/acres_text.py`** - Perspective Acres Label
- Calculate property centroid and major axis orientation
- Project acres text with **full 3D perspective** (not billboard)
- Text follows ground plane slope and vanishing point
- Configurable:
  - Font family (default: Arial Black)
  - Font size (scales with property size)
  - Color (default: yellow #FFFF00)
  - Stroke (default: black outline, 3px)

**4. `compositor/street_labels.py`** - Billboard Street Text
- Parse street label data from sidecar JSON `labels` array
- For each label:
  - Project 3D anchor point to 2D screen position
  - Calculate text rotation to face camera (billboard style)
  - Render text perpendicular to ground plane
- Configurable:
  - Font family (default: Arial Bold)
  - Font size (default: 32px, scaled by distance from camera)
  - Text color and stroke (default: white with black outline)

**5. `compositor/compose.py`** - Main Composition Pipeline
```python
def compose_final_image(png_path, sidecar_path, output_path, config):
    # 1. Load base PNG
    # 2. Load sidecar JSON
    # 3. Draw boundary overlay
    # 4. Draw street labels
    # 5. Draw acres text (centered on property)
    # 6. Save final PNG
```

**6. `config.json`** - Styling Configuration
```json
{
  "boundary": {
    "stroke_width": 10,
    "stroke_color": "#FFFF00",
    "inner_shadow": {
      "color": "#000000",
      "blur": 8,
      "offset": [2, 2]
    },
    "outer_glow": {
      "color": "#FFFF00",
      "blur": 4
    }
  },
  "acres_text": {
    "font_family": "Arial Black",
    "font_size": 72,
    "color": "#FFFF00",
    "outline_width": 3,
    "outline_color": "#000000",
    "use_perspective": true
  },
  "street_text": {
    "font_family": "Arial",
    "font_size": 28,
    "color": "#FFFFFF",
    "outline_width": 4,
    "outline_color": "#000000",
    "billboard_style": true
  }
}
```

---

## n8n Integration

**Workflow Steps**:
1. **Trigger**: Robotic Property Photographer completes render job
2. **Execute Python Code Node**:
   - Input: `png_path`, `sidecar_path`, `output_dir`
   - Script: `python compositor/compose.py --input {sidecar_path} --output {output_dir}`
   - Output: Path to final composed PNG
3. **Upload to Delivery**: Use SureCart digital download integration

**Example n8n Python Node**:
```python
from compositor.compose import compose_final_image
import json

# Inputs from previous node
png_path = items[0].json['png_path']
sidecar_path = items[0].json['sidecar_path']
output_path = '/output/final.png'

# Load config
with open('config.json') as f:
    config = json.load(f)

# Compose final image
compose_final_image(png_path, sidecar_path, output_path, config)

return [{'json': {'final_image': output_path}}]
```

---

## Technical Details

### 3D → 2D Projection Math

The sidecar JSON provides `view` and `projection` matrices in column-major order. To project a 3D point to screen space:

```python
import numpy as np

def world_to_screen(point_3d, view_matrix, proj_matrix, viewport):
    """
    Project a 3D world point to 2D screen coordinates.
    
    Args:
        point_3d: [x, y, z] in world ECEF coordinates
        view_matrix: 4x4 view matrix (column-major)
        proj_matrix: 4x4 projection matrix (column-major)
        viewport: {"width": 2048, "height": 1536}
    
    Returns:
        [screen_x, screen_y] in pixel coordinates
    """
    # Convert to homogeneous coordinates
    point_4d = np.array([point_3d[0], point_3d[1], point_3d[2], 1.0])
    
    # Apply view transform (world → camera space)
    view_space = np.dot(view_matrix.reshape(4, 4), point_4d)
    
    # Apply projection (camera → clip space)
    clip_space = np.dot(proj_matrix.reshape(4, 4), view_space)
    
    # Perspective divide (clip → NDC)
    ndc = clip_space[:3] / clip_space[3]
    
    # NDC → screen space
    screen_x = (ndc[0] + 1.0) * 0.5 * viewport['width']
    screen_y = (1.0 - ndc[1]) * 0.5 * viewport['height']
    
    return [screen_x, screen_y]
```

### Billboard Text Calculation

For camera-facing text that remains **perpendicular to the ground plane** (horizontal rotation only, no vertical tilt):

```python
def calculate_billboard_rotation(camera_local_enu):
    """
    Calculate rotation angle for billboard text.
    Text rotates to face camera horizontally but stays perpendicular to ground.
    
    Args:
        camera_local_enu: Camera direction vector in local ENU frame
    
    Returns: rotation angle in degrees (Z-axis rotation only)
    """
    # Project camera direction onto ground plane (ignore Z component)
    dx = camera_local_enu['direction']['x']  # East component
    dy = camera_local_enu['direction']['y']  # North component
    
    # Calculate horizontal angle (around Z-axis only)
    angle = np.arctan2(dx, dy)  # Angle from North
    return np.degrees(angle)
```

---

## Verification Plan

### Unit Tests
- **Projection Accuracy**: Verify that projecting boundary points matches expected screen positions
- **Matrix Parsing**: Ensure column-major matrices are correctly reshaped
- **Billboard Rotation**: Verify text orientation for cardinal views (0°, 90°, 180°, 270°)

### Integration Tests
1. Run compositor on sample sidecar JSON from "west" view
2. Verify boundary overlay aligns with property in base PNG
3. Verify street labels are legible and positioned over roads
4. Test with multiple property sizes (2.40 to 870 acres)

### Visual Verification
- Compare composed output to manual Photoshop results
- Check for:
  - Boundary alignment with rendered imagery
  - Text legibility at all camera angles
  - Consistent styling across all 5 views

---

## Dependencies

**Python Packages**:
- `Pillow` - Image manipulation and drawing
- `numpy` - Matrix operations
- `pycairo` - Advanced text rendering with effects

**n8n Environment**:
- External Python runner (configured)
- Bind mounts available at:
  - `/data/shared` - for input/output file exchange
  - `/data/generated` - for final composed images
- Access to sidecar JSON and PNG outputs from Robotic Property Photographer

---

## Next Steps

1. Add `numpy` to n8n runner Dockerfile and rebuild
2. Create `compositor/` module directory (in `/data/shared/compositor/`)
3. Implement core projection and rendering functions
4. Test with sample data from Robotic Property Photographer
5. Integrate into n8n workflow
6. Iterate on styling based on visual results
