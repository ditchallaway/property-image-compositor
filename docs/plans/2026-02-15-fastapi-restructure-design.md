# Design: Restructure Compositor as Independent FastAPI Microservice

## Problem

The compositor currently runs as a stateless script inside n8n's Python runner — a locked-down Alpine container with fixed dependencies, no HTTP server, no database, and no runtime `pip install`. These constraints create constant "side quests" for anyone working on the code: every AI agent and developer must internalize a list of hard constraints that have nothing to do with image composition.

## Solution

Extract the compositor into an **independent Python app** with a **FastAPI REST API**, running in its own Docker container on the same network as n8n and the Robotic Property Photographer.

### What Changes

| Before | After |
|---|---|
| n8n Python runner script | Standalone FastAPI service |
| Alpine-based `runners/Dockerfile` (n8n's) | Debian-based `Dockerfile` (ours) |
| CLI entrypoint (`python compose.py --png ... --json ...`) | HTTP entrypoint (`POST /compose`) |
| Fixed deps, no runtime pip | Own `requirements.txt`, full control |
| Invoked per-image by n8n Code node | Long-running container, called via HTTP |

### What Stays the Same

- Core compositor modules: `compose.py`, `boundary.py`, `labels.py`, `project.py`, `grid.py`, `psd_export.py`
- Dependencies: `numpy`, `pillow`, `pycairo`, `pytoshop`, `six`
- Input/output: PNG + sidecar JSON in → composed image out
- Shared volumes for file I/O between containers

---

## Architecture

```
┌──────────┐   POST /compose    ┌──────────────────┐
│   n8n    │ ─────────────────▸ │   compositor     │
│ workflow │                    │   (FastAPI)      │
└──────────┘                    │   :8000          │
                                │                  │
┌──────────┐   (can also call)  │  src/compositor/ │
│ Robotic  │ ─────────────────▸ │  src/api/main.py │
│ Property │                    └──────────────────┘
│ Photog.  │                           │
└──────────┘                     /data/shared (volume)
                                 /data/generated (volume)
```

All containers share a Docker network (`compositor_net`). File paths reference shared volumes.

---

## API Design

### `POST /compose`

Request body (JSON):
```json
{
  "png_path": "/data/shared/west.png",
  "json_path": "/data/shared/west.json",
  "output_path": "/data/generated/composed_west.png",
  "output_format": "png",
  "stage": 2
}
```

Response (success):
```json
{
  "status": "ok",
  "output_path": "/data/generated/composed_west.png"
}
```

Response (error):
```json
{
  "status": "error",
  "detail": "File not found: /data/shared/west.png"
}
```

### `GET /health`

```json
{ "status": "healthy" }
```

---

## File Structure (After)

```
property-image-compositor/
├── src/
│   ├── api/
│   │   └── main.py          # FastAPI app + endpoints
│   └── compositor/
│       ├── __init__.py
│       ├── compose.py        # (unchanged core logic)
│       ├── boundary.py
│       ├── labels.py
│       ├── project.py
│       ├── grid.py
│       └── psd_export.py
├── scripts/                   # Test harnesses (updated)
├── test_data/
├── output/
├── requirements.txt           # [NEW] pinned deps
├── Dockerfile                 # [UPDATED] standalone FastAPI
├── docker-compose.yml         # [UPDATED] compositor as service
├── README.md                  # [UPDATED] new architecture
├── IMPLEMENTATION_PLAN.md     # [UPDATED]
└── TASK.md                    # [UPDATED]
```

Removed: `runners/Dockerfile` (n8n runner artifact, no longer needed).

---

## Docker Setup

### Dockerfile
- Base: `python:3.10-slim` (already in use for dev)
- Install system deps (cairo, pango, etc.)
- `pip install -r requirements.txt` (including `fastapi`, `uvicorn`)
- `CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]`

### docker-compose.yml
- `compositor` service: builds from `Dockerfile`, exposes `8000`, mounts `/data/shared` and `/data/generated`
- `nginx` service: serves output directory for browsing (same as before)
- Shared network: `compositor_net`

---

## Migration Path for n8n

n8n workflows that currently call the Python runner script will be updated to use an **HTTP Request node** instead:

```
Before: n8n Code Node → python3 compose.py --png ... --json ...
After:  n8n HTTP Request Node → POST http://compositor:8000/compose { ... }
```

This is a simpler n8n node to configure and debug.
