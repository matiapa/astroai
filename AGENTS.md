# AGENTS.md

This file provides agent-focused guidance for the AstroIA repository. The project contains two independent apps:
- Backend: `backend/`
- Frontend: `frontend/`

Each app has a detailed README. Use those for deep setup and app-specific workflows:
- `backend/README.md`
- `frontend/README.md`

## Project Overview

AstroIA (AstroAI) is a two-application system for AI-guided astronomy:
- The backend analyzes sky images, identifies celestial objects, and generates narration/audio.
- The frontend (AstroGuide) is a Flutter app that captures images, streams analysis results, and provides a guided experience.

The apps communicate over HTTP (SSE for analysis updates and an A2A agent interface).

## Repository Structure

```
.
├── backend/      FastAPI service, AI agents, image analysis, deployment assets
├── frontend/     Flutter app (Android + Web)
├── README.md     Human-oriented project overview
└── AGENTS.md     Agent-oriented instructions (this file)
```

## Quick Start (Local Dev)

Run the apps independently. Typical local workflow:
1. Start backend API (see `backend/README.md`).
2. Configure frontend API base URL to point at the backend.
3. Run the frontend app (see `frontend/README.md`).

## Commands

These are the most common entry points. Use the app READMEs for full detail.

Backend:
- Install deps: `pip install -r requirements.txt`
- Run API: `python -m src.api.server`
- Tests: `python -m unittest discover -s tests`

Frontend:
- Install deps: `flutter pub get`
- Run web: `flutter run -d chrome --dart-define-from-file=.env`
- Run Android: `flutter run -d <device_id> --dart-define-from-file=.env`
- Tests: `flutter test`
- Lint: `flutter analyze`

## Environment Notes

Backend:
- Requires a Google API key for Gemini (`GOOGLE_API_KEY`) to enable narration and TTS.
- Optional Astrometry.net key if using that plate-solving method.

Frontend:
- Uses `.env` with `API_BASE_URL` and `A2A_AGENT_URL` to connect to backend.

## Code Style and Conventions

Follow the app-specific conventions described in each README.
Keep changes scoped to a single app whenever possible to reduce review and testing surface.

## Testing Guidance

Run only the tests relevant to the area you changed:
- Backend changes: run backend unit tests.
- Frontend changes: run Flutter tests and analyzer.

If you change shared docs or config only, tests are optional.

## Where to Look First

Backend:
- API entry: `backend/src/api/server.py`
- Agents: `backend/agents/`
- Image pipeline: `backend/src/tools/capture_sky/`

Frontend:
- Feature modules: `frontend/lib/features/`
- Core config/theme: `frontend/lib/core/`
- Localization: `frontend/lib/l10n/`

## Deployment

Deployment is app-specific:
- Backend: Docker + Terraform (Cloud Run)
- Frontend: Flutter web build + Firebase hosting

Refer to each app README for full deployment steps.
