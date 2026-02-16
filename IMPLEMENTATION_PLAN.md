# Implementation Plan — Property Image Compositor

Standalone FastAPI microservice for composing property images from 3D renders.

---

## Module Architecture

### 1. `src/api/main.py` (REST API)

- FastAPI app with `POST /compose` and `GET /health`
- Validates requests with Pydantic models
- Delegates to `compose_image()` from the compositor module

### 2. `src/compositor/project.py` (Projection Engine)

- Consumes the `matrices` and `metadata` from the sidecar JSON.
- **Math**: Column-major 4x4 matrix multiplication for World → Camera → Clip → NDC → Screen.

### 3. `src/compositor/boundary.py` (Visual Styling)

- Multi-layer draw logic to simulate a 3D tube:
  - Base layer: thick yellow stroke.
  - Inner layer: thinner dark stroke for shadow.
  - Highlight: thin white/bright yellow stroke on top.

### 4. `src/compositor/labels.py` (Text Management)

- **Acres**: Perspective transform (warping) to match terrain slope.
- **Streets**: Billboard rotation (facing camera, vertical to ground).

### 5. `src/compositor/compose.py` (Pipeline)

- Layer-based composition orchestrator
- Loads background PNG, builds overlay layers, exports flat PNG or layered PSD

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

## Deployment

The service runs as a Docker container on the same network as n8n and other services.

**Docker Compose** starts the compositor and an nginx container for output browsing:

```bash
docker compose up --build -d
```

**n8n Integration**: Use an HTTP Request node to `POST http://compositor:8000/compose` with the PNG/JSON paths.
