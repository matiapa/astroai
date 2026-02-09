# AstroAI Backend — Agent Guide

This document is for AI agents working in this repo. It mirrors the README but is optimized for fast, correct automation.

## Mission

Analyze astronomical images, identify objects, and generate narrated explanations (text + optional audio) via a FastAPI service and Google ADK agents.

## Key Entry Points

- API server: `src/api/server.py`
- Analyze pipeline (SSE): `src/api/analyze/controller.py`
- Core image tool: `src/tools/capture_sky/tool.py`
- AstroAI agent: `agents/astro_guide/agent.py`
- Observation planner agent: `agents/observation_planner/agent.py`
- OpenAPI spec: `docs/openapi.yaml`

## Runtime Overview

High-level `/analyze` flow:
1. Plate solving (`custom_remote` or `astrometry_net`)
2. Object detection in the image
3. SIMBAD lookups
4. Gemini narration
5. Gemini TTS audio
6. SSE events streamed to client

A2A agent is mounted at `/a2a`.

## Configuration (Env Vars)

Load from `.env` via `python-dotenv`.

Required:
- `GOOGLE_API_KEY` (Gemini narration + TTS)

Optional/conditional:
- `GEMINI_API_KEY` (alias used in config resolution)
- `ASTROMETRY_API_KEY` (required when `PLATE_SOLVING_METHOD=astrometry_net`)
- `GOOGLE_CSE_ID` (for Google Custom Search tool)

Common defaults (see `.env.default`):
- `PLATE_SOLVING_METHOD=custom_remote`
- `ASTROMETRY_API_URL=http://ec2-3-145-73-178.us-east-2.compute.amazonaws.com/solve`
- `PLATE_SOLVING_TIMEOUT=30`
- `PLATE_SOLVING_USE_CACHE=false`
- `WEBCAM_INDEX=0`
- `OBJECT_DETECTOR=contrast_detector`
- `MAX_QUERY_OBJECTS=10`
- `SIMBAD_SEARCH_RADIUS=10`
- `LOGS_DIR=logs`
- `STORAGE_DIR=/mnt/data`
- `VERBOSE=True`
- `TEST_MODE=false`
- `API_HOST=0.0.0.0`
- `API_PORT=8000`
- `PUBLIC_API_URL=http://localhost:8000`

Notes for agents:
- `PLATE_SOLVING_USE_CACHE` and `VERBOSE` are case-sensitive checks in code.
- Audio is saved to `${STORAGE_DIR}/audios/`.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.default .env
python -m src.api.server
```

Default API: `http://localhost:8000`.

## API (SSE)

`POST /analyze` streams events:
- `analyzing_image`
- `analysis_complete` (plate solving + objects)
- `generating_narration`
- `narration_complete` (title/text/legends)
- `generating_audio`
- `audio_complete` (audio_url)
- `error`

Example:
```bash
curl -N -X POST \
  -F "image=@/path/to/your_image.jpg" \
  -F "language=es" \
  http://localhost:8000/analyze
```

## Agents (Google ADK)

- `astro_guide` uses `SkyCaptureTool` + search + `observation_planner` agent.
- `observation_planner` uses conditions, catalog search, and visibility tools.

Run:
```bash
adk run astro_guide
adk web --port 8001
```

## Scripts

- `scripts/run_capture_sky.py` list cameras, capture, or run full analysis
- `scripts/complete_cache.py` fill in missing SIMBAD data for cached items

## Docker + Cloud Run

Docker:
```bash
docker build -t AstroAI-backend .
docker run --rm -p 8080:8080 --env-file .env AstroAI-backend
```

Cloud Run + Terraform:
- Infra in `terraform/`
- Use `Makefile` targets: `make check-env`, `make deploy`, etc.

## Tests

```bash
python -m unittest discover -s tests
```

## Safety / Guardrails for Agents

- Do not hardcode API keys or secrets.
- Avoid long-running or external network calls unless explicitly requested.
- Prefer existing scripts/utilities over rewriting logic.
- Keep outputs deterministic (e.g., avoid non-deterministic prompts unless asked).

## References

- Agents.md spec: [https://agents.md/](https://agents.md/)
