# Implementation Plan - Property Image Compositor

> **⚠️ ARCHITECTURE ALERT**: This is the second component of the **Virtual Drone Photography for Real Estate** service. It runs EXCLUSIVELY in the **n8n Python Runner** environment.

## n8n Environment Constraints

1. **Stateless**: The script is invoked per image. It must be idempotent.
2. **File System**: Access inputs at `/data/shared` and write outputs to `/data/generated`.
3. **Dependencies**: `Pillow`, `PyCairo`, and `NumPy` are provided by the n8n runner container.

---

## Proposed Changes (Python Module)

The module should be structured to be easily importable into an n8n "Code" node or executed via a command-line script.

### 1. `project.py` (Projection Engine)
- Consumes the `matrices` and `metadata` from the sidecar JSON.
- **Math**: Column-major 4x4 matrix multiplication for World → Camera → Clip → NDC → Screen.

### 2. `boundary.py` (Visual Styling)
- Multi-layer draw logic to simulate a 3D tube:
  - Base layer: thick yellow stroke.
  - Inner layer: thinner dark stroke for shadow.
  - Highlight: thin white/bright yellow stroke on top.

### 3. `labels.py` (Text Management)
- **Acres**: Perspective transform (warping) to match terrain slope.
- **Streets**: Billboard rotation (facing camera, vertical to ground).

---

## Technical Details: Matrix Projection

The sidecar JSON specifies `view` and `projection` matrices.

```python
import numpy as np

def project_point(point_wgs84, sidecar):
    # ECEF is already provided in boundary_3d/local_enu
    # Use sidecar['matrices']['view'] and sidecar['matrices']['projection']
    pass
```

---

## Deployment in n8n

The n8n workflow should pass the absolute path of the PNG and JSON files to the script.

**Example execution**:
`python3 compose.py --png /data/shared/west.png --json /data/shared/west.json --output /data/generated/final_west.png`
