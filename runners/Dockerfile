# runners/Dockerfile
# Optimized for Virtual Drone Photography Compositor
FROM n8nio/runners:latest

USER root

# Install build dependencies for NumPy and PyCairo
# We use --no-cache to keep the image small ("keeping it chill")
RUN apk add --no-cache \
    build-base \
    python3-dev \
    cairo-dev \
    pango-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    openblas-dev

# Install Python dependencies
# NumPy is critical for the matrix projection math
RUN pip install --no-cache-dir \
    numpy \
    pillow \
    pycairo

# Switch back to the non-root user used by n8n
USER node
