# Task Checklist — Property Image Compositor

## Completed (Pre-Restructure)
- [x] Matrix-based 3D → 2D projection
- [x] Boundary overlay renderer
- [x] Billboard text placement system
- [x] Styling configuration (fonts, colors, effects)
- [x] Main composition pipeline
- [x] Stage 1 (Lines Only) rendering
- [x] PSD layered export

## Restructure: FastAPI Microservice
- [x] Write design doc
- [x] Update project documents (README, IMPLEMENTATION_PLAN, TASK)
- [ ] Create `requirements.txt`
- [ ] Update `Dockerfile` for standalone FastAPI
- [ ] Update `docker-compose.yml`
- [ ] Create FastAPI app (`src/api/main.py`)
- [ ] Remove `runners/Dockerfile`
- [ ] Verify Docker build
- [ ] Verify health endpoint
- [ ] Verify compose endpoint with test data
- [ ] Verify output via nginx

## Future
- [ ] Verify Stage 1 vs Stage 2 output
- [ ] Batch compose endpoint (multiple views)
- [ ] Async processing with job status polling
