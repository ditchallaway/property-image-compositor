# Local Development Environment

This directory structure supports local Docker-based development:

## Quick Start

1. **Copy test data from renderer:**
   ```bash
   # From Robotic-Property-Photographer directory
   cp public/snapshots/order_12345/cust_98765/*.{png,json} ../property-image-compositor/test_data/raw/
   ```

2. **Start the environment:**
   ```bash
   docker-compose up -d
   ```

3. **Run the test harness:**
   ```bash
   docker-compose exec compositor python3 scripts/compose_test.py
   ```

4. **View results:**
   Open `http://localhost:8080/output/` in your browser

## Directory Structure

- `test_data/raw/` - Input PNGs and JSON sidecars from the renderer
- `output/` - Composed output images (visible at localhost:8080)
- `scripts/compose_test.py` - Local test harness
- `docker-compose.yml` - Development stack (compositor + nginx)

## Development Workflow

1. Edit Python code in `src/compositor/`
2. Re-run test harness (no rebuild needed - code is bind-mounted)
3. Refresh browser to see new outputs
4. Iterate until alignment is perfect
