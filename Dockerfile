# Dockerfile
# Property Image Compositor — Standalone FastAPI Microservice
FROM python:3.10-slim

USER root

# 1. Install Runtime & Build Dependencies
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
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# 3. Create app user and directory
RUN useradd -m appuser
WORKDIR /app

# 4. Copy source code
COPY src/ /app/src/

# 5. Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]