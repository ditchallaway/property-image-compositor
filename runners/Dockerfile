# runners/Dockerfile
# Optimized for "Virtual Drone Photography" Image Composition
FROM n8nio/runners:latest

USER root

# 1. Install Runtime Libraries
# pango/cairo = essential for high-quality text & graphics
# openblas = acceleration for NumPy matrix math
RUN apk add --no-cache \
    cairo \
    pango \
    libjpeg-turbo \
    libpng \
    freetype \
    openblas \
    libgcc

# 2. Install Build Dependencies (Temporary)
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    python3-dev \
    cairo-dev \
    pango-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    openblas-dev \
    \
    # 3. Install Python packages
    # numpy: heavy lifting for 3D -> 2D projection
    # pillow: base image handling/saving
    # pycairo: vector-grade text and boundary stroke rendering
    && pip install --no-cache-dir \
        numpy \
        pillow \
        pycairo \
    \
    # 4. Clean up build dependencies
    && apk del .build-deps \
    && rm -rf /var/cache/apk/*

USER node
