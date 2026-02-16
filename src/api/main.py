"""
main.py — FastAPI REST API for the Property Image Compositor.

Endpoints:
    POST /compose  — Compose a property image from a raw render + sidecar JSON.
    GET  /health   — Health check.
"""
import os
import time
import traceback
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.compositor.compose import compose_image


# ─── App ───

app = FastAPI(
    title="Property Image Compositor",
    description="Composes property images from 3D renders with boundary overlays, "
                "street labels, and acres text.",
    version="1.0.0",
)


# ─── Models ───

class OutputFormat(str, Enum):
    png = "png"
    psd = "psd"
    both = "both"


class ComposeRequest(BaseModel):
    png_path: str = Field(..., description="Path to raw input PNG")
    json_path: str = Field(..., description="Path to sidecar JSON with matrices/metadata")
    output_path: str = Field(..., description="Path for the composed output file")
    config_path: Optional[str] = Field(None, description="Optional path to style config JSON")
    output_format: OutputFormat = Field(OutputFormat.png, description="Output format")
    stage: int = Field(2, ge=1, le=2, description="1 = lines only, 2 = full composition")

    model_config = {"json_schema_extra": {
        "examples": [{
            "png_path": "/app/test_data/raw/west.png",
            "json_path": "/app/test_data/raw/west.json",
            "output_path": "/app/output/composed_west.png",
            "output_format": "png",
            "stage": 2,
        }]
    }}


class ComposeResponse(BaseModel):
    status: str
    output_path: str
    elapsed_ms: int


class HealthResponse(BaseModel):
    status: str


# ─── Endpoints ───

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check."""
    return HealthResponse(status="healthy")


@app.post("/compose", response_model=ComposeResponse)
async def compose(req: ComposeRequest):
    """Compose a property image from a raw render and sidecar JSON."""

    # Validate input files exist
    if not os.path.isfile(req.png_path):
        raise HTTPException(status_code=400, detail=f"PNG file not found: {req.png_path}")
    if not os.path.isfile(req.json_path):
        raise HTTPException(status_code=400, detail=f"JSON file not found: {req.json_path}")
    if req.config_path and not os.path.isfile(req.config_path):
        raise HTTPException(status_code=400, detail=f"Config file not found: {req.config_path}")

    # Ensure output directory exists
    output_dir = os.path.dirname(req.output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Run compositor
    start = time.time()
    try:
        compose_image(
            png_path=req.png_path,
            json_path=req.json_path,
            output_path=req.output_path,
            config_path=req.config_path,
            output_format=req.output_format.value,
            stage=req.stage,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Composition failed: {e}")

    elapsed_ms = int((time.time() - start) * 1000)

    return ComposeResponse(
        status="ok",
        output_path=req.output_path,
        elapsed_ms=elapsed_ms,
    )
