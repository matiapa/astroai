# AstroAI Backend

AstroAI is an AI-powered backend that analyzes astronomical images, identifies celestial objects, and generates narrated explanations with optional audio. It exposes a FastAPI service, includes two Google ADK agents (AstroAI and Observation Planner), and ships Docker/Terraform assets for deployment.

**What it does**
- Plate-solves telescope images to recover sky coordinates
- Detects point sources and queries SIMBAD for object identification
- Uses Gemini to generate structured narration and TTS audio
- Streams progress and results over Server-Sent Events (SSE)
- Exposes an A2A agent interface at `/a2a`

**Primary components**
- API server: `src/api/server.py`
- AstroAI agent: `agents/astro_guide/agent.py`
- Observation planner agent: `agents/observation_planner/agent.py`
- Image analysis pipeline: `src/tools/capture_sky/`
- OpenAPI spec: `docs/openapi.yaml`

## Architecture overview

High-level flow for `/analyze`:
1. Plate solving via `custom_remote` or `astrometry_net`
2. Object detection in the image
3. SIMBAD lookups for identified objects
4. Gemini narration generation
5. Gemini TTS audio generation

Key services and tools:
- `SkyCaptureTool` handles plate solving, detection, SIMBAD querying, and image annotation
- `NarrationGenerator` produces JSON narration using Gemini
- `TTSService` generates WAV audio with Gemini TTS
- Observation planning tools provide sky conditions, catalog search, and visibility windows

## Requirements

- Python 3.10+ (Docker image uses 3.10)
- OS packages for OpenCV (installed in the Docker image)
- Google API key for Gemini (`GOOGLE_API_KEY`)
- Optional: Astrometry.net API key if `PLATE_SOLVING_METHOD=astrometry_net`

## Quickstart (local)

1. Create and activate a virtual environment.
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.
```bash
pip install -r requirements.txt
```

3. Configure environment variables.
```bash
cp .env.default .env
```

4. Run the API server.
```bash
python -m src.api.server
```

The API listens on `http://localhost:8000` by default.

## Configuration

The backend reads configuration from environment variables or `.env` using `python-dotenv`. Copy `.env.default` and adjust as needed.

| Variable | Default | Description |
| --- | --- | --- |
| `GOOGLE_API_KEY` | (empty) | Required for Gemini narration and TTS |
| `GEMINI_API_KEY` | (empty) | Optional alias for Gemini key used in config resolution |
| `GOOGLE_CSE_ID` | (empty) | Required for Google Custom Search (if used) |
| `ASTROMETRY_API_KEY` | (empty) | Required when `PLATE_SOLVING_METHOD=astrometry_net` |
| `ASTROMETRY_API_URL` | `http://ec2-3-145-73-178.us-east-2.compute.amazonaws.com/solve` | Remote plate-solving endpoint for `custom_remote` |
| `PLATE_SOLVING_METHOD` | `custom_remote` | `custom_remote` or `astrometry_net` |
| `PLATE_SOLVING_TIMEOUT` | `30` | Plate-solving timeout (seconds) |
| `PLATE_SOLVING_USE_CACHE` | `false` | Cache WCS results (case-sensitive string check in code) |
| `WEBCAM_INDEX` | `0` | Camera index for capture scripts |
| `OBJECT_DETECTOR` | `contrast_detector` | Detection strategy (current implementation) |
| `MAX_QUERY_OBJECTS` | `10` | Max objects to query from SIMBAD |
| `SIMBAD_SEARCH_RADIUS` | `10` | Radius in arcseconds |
| `LOGS_DIR` | `logs` | Directory for logs and artifacts |
| `STORAGE_DIR` | `/mnt/data` | Storage root for audio and cache |
| `VERBOSE` | `True` | Verbose logging toggle |
| `TEST_MODE` | `false` | Skip Gemini identification step in `/analyze` |
| `API_HOST` | `0.0.0.0` | API host bind address |
| `API_PORT` | `8000` | API port |
| `PUBLIC_API_URL` | `http://localhost:8000` | Base URL used for audio links |

Notes:
- The code treats `PLATE_SOLVING_USE_CACHE` and `VERBOSE` as case-sensitive checks. Use `True`/`False` or `true`/`false` consistently as shown in `.env.default`.
- Audio files are written to `${STORAGE_DIR}/audios/`.

## API

Base URL: `http://localhost:8000`

Endpoints:
- `GET /` health check
- `POST /analyze` analyze image (SSE)
- `GET /audio/{filename}` download generated WAV audio
- `GET /a2a/...` A2A agent interface (mounted sub-app)

OpenAPI spec is available at `docs/openapi.yaml`.

### `/analyze` SSE events

The response is a stream of SSE events. Event names:
- `analyzing_image`
- `analysis_complete` with `plate_solving` and `identified_objects`
- `generating_narration`
- `narration_complete` with `title`, `text`, and `object_legends`
- `generating_audio`
- `audio_complete` with `audio_url`
- `error` with error details

Example:
```bash
curl -N -X POST \
  -F "image=@/path/to/your_image.jpg" \
  -F "language=es" \
  http://localhost:8000/analyze
```

## Agents

The repository provides two Google ADK agents:
- `astro_guide` for image-based sky narration and object context
- `observation_planner` for planning observation sessions

Run the ADK web UI (optional):
```bash
adk web --port 8001
```

Run an agent directly:
```bash
adk run astro_guide
```

## Scripts

- `scripts/run_capture_sky.py` capture a webcam frame and run analysis
- `scripts/complete_cache.py` fill missing SIMBAD details in cached results
- `scripts/deploy.sh` deployment helper (see Terraform section)

List available cameras:
```bash
python scripts/run_capture_sky.py --list-cameras
```

Capture a single frame:
```bash
python scripts/run_capture_sky.py --capture --camera-index 0 --output captured.png
```

## Docker

Build and run locally:
```bash
docker build -t AstroAI-backend .
docker run --rm -p 8080:8080 --env-file .env AstroAI-backend
```

Note: The container listens on `API_PORT`, and Terraform config sets it to `8080` for Cloud Run.

## Deployment (GCP Cloud Run)

The `Makefile` and `terraform/` directory automate deployment.

Typical flow:
```bash
make check-env
make check-tfvars
make setup-registry
make setup-bucket
make deploy
```

Terraform expects a `terraform/terraform.tfvars` file. Use `terraform/terraform.tfvars.example` as a template.

## Testing

Run unit tests:
```bash
python -m unittest discover -s tests
```

## Project structure

```
.
├── agents/                 ADK agent definitions
├── docs/                   OpenAPI spec
├── scripts/                Utility scripts
├── src/                     API, services, tools
├── terraform/              Cloud Run infrastructure
├── tests/                  Unit tests
├── Dockerfile
├── Makefile
└── requirements.txt
```

## License

No explicit license file is present in this repository. If you intend to open-source or redistribute, add a `LICENSE` file and update this section.
