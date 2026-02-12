# Dockerfile
# Optimized for "Virtual Drone Photography" Image Composition
# Switched to standard Python base for reliable builds
FROM python:3.10-slim

USER root

# 1. Install Runtime & Build Dependencies
# Combine apt-get update/install/clean to keep layers small
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential \
    pkg-config \
    \
    # Graphics libraries (runtime + dev)
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    \
    # Math optimization (numpy)
    libopenblas-dev \
    \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python packages
# numpy: heavy lifting for 3D -> 2D projection
# pillow: base image handling/saving
# pycairo: vector-grade text and boundary stroke rendering
RUN pip install --no-cache-dir \
    numpy \
    pillow \
    pycairo

# Create app user
RUN useradd -m appuser
USER appuser
