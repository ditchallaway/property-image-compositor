# runners/Dockerfile
# Optimized for Virtual Drone Photography + GIS Utility
FROM n8nio/runners:latest

# Switch to root to install system dependencies
USER root

# 1. Install Runtime Libraries (Permanent)
# These are the shared libraries needed by Python packages at runtime.
RUN apk add --no-cache \
    gdal \
    geos \
    proj \
    cairo \
    pango \
    libjpeg-turbo \
    libpng \
    freetype \
    libxml2 \
    openblas

# 2. Install Build Dependencies (Temporary)
# These are only needed to compile/build the Python wheels.
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    gcc \
    python3-dev \
    musl-dev \
    gdal-dev \
    geos-dev \
    proj-dev \
    cairo-dev \
    pango-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    libxml2-dev \
    openblas-dev \
    \
    # 3. Install Python packages
    && pip install --no-cache-dir \
        numpy \
        shapely \
        rasterio \
        pillow \
        pycairo \
    \
    # 4. Clean up build dependencies to "keep it chill"
    && apk del .build-deps \
    && rm -rf /var/cache/apk/*

# Switch back to the non-root user used by n8n
USER node
