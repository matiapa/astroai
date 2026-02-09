# AstroA

AstroAI is a project that brings AI-guided astronomy to life. The backend analyzes sky images, identifies celestial objects, and generates narration. The frontend delivers a mobile-first experience that captures images, displays results, and enables conversational guidance.

This root README covers the overall project. Each app is fully documented in its own README:
- Backend: `backend/README.md`
- Frontend: `frontend/README.md`

## Project Overview

AstroAI is split into two independent apps that communicate over HTTP:
- `backend/` exposes a FastAPI service for image analysis, narration, and the A2A agent interface.
- `frontend/` is a Flutter app (Android APK + PWA) that captures sky images, streams analysis results, and provides a guided experience.

Typical flow:
1. User captures an image in the frontend.
2. Frontend sends the image to the backend `/analyze` endpoint (SSE stream).
3. Backend returns object detections, narration, and optional audio.
4. Frontend renders hotspots, playback, and chat.

## Repository Structure

```
.
├── backend/      FastAPI service, AI agents, image analysis, deployment assets
├── frontend/     Flutter app (Android + Web)
└── README.md     Project overview (this file)
```

## Getting Started

Because each app is independent, follow the setup steps in the app-specific READMEs:
- Backend setup and API usage: `backend/README.md`
- Frontend setup and run targets: `frontend/README.md`

High-level prerequisites:
- Backend: Python 3.10+, Google API key for Gemini
- Frontend: Flutter SDK (stable), Android SDK and/or Chrome

## Development Workflow

Common pattern for local development:
1. Start the backend API (see `backend/README.md`).
2. Configure the frontend to point at the backend base URL.
3. Run the frontend app (see `frontend/README.md`).

## Deployment

Deployment is handled separately per app:
- Backend: Docker + Terraform for Cloud Run
- Frontend: Flutter web build + Firebase hosting

See each app README for the full deployment steps and required environment variables.

## Contributing

1. Create a feature branch.
2. Follow the app-specific lint/test commands before opening a PR.
3. Keep changes scoped to one app when possible to simplify review.

## License

No license file is present in this repository. Treat this project as proprietary unless a license is added.
