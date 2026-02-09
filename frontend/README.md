# AstroAI (AstroAI Frontend)

AstroAI is a mobile-first Flutter application (Android APK + PWA) that turns nighttime sky viewing into an interactive, narrated experience. Users capture a sky image, the app analyzes it via an API, reveals identified celestial objects with interactive hotspots, and enables a guided chat with an AI agent.

**Core flow**
```
Capture → Analyze → Reveal → Converse
```

**Platforms**
- Android (APK)
- Web (PWA)

## Features
- Camera capture with manual controls and gallery upload
- AI-powered sky analysis with progressive SSE updates
- Interactive object hotspots on results imagery
- Audio narration playback
- Conversational AI chat (A2A protocol)
- Discovery history (Logbook) with local persistence
- Accessibility-first, dark OLED-optimized UI
- Internationalization (EN/ES)

## Tech Stack
- Flutter + Dart (latest stable)
- State management: Riverpod
- Navigation: GoRouter
- Local storage: Hive (including web)
- Networking: Dio
- Audio: just_audio + record
- Chat: A2A protocol with Flutter AI Toolkit

## Architecture Overview
- Feature-based organization under `lib/features/*`
- Shared infrastructure under `lib/core/*`
- API analysis via `/analyze` (SSE stream)
- A2A JSON-RPC for chat

**Key directories**
- `lib/core/` shared navigation, theme, config
- `lib/features/observatory/` camera and capture UI
- `lib/features/results/` analysis display + narration
- `lib/features/chat/` A2A chat experience
- `lib/features/logbook/` local history gallery
- `lib/features/settings/` user preferences
- `lib/l10n/` localization resources

## Requirements
- Flutter SDK (stable)
- Dart SDK (bundled with Flutter)
- Android SDK + emulator/device (for APK)
- Chrome (for web)
- Firebase CLI (only for deployment)

## Setup
1. Install dependencies:
   ```bash
   flutter pub get
   ```
2. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your local API endpoints.

## Run (Development)
**Web (Chrome)**
```bash
flutter run -d chrome --dart-define-from-file=.env
```

**Android**
```bash
flutter run -d <device_id> --dart-define-from-file=.env
```

VS Code launch configs already include `--dart-define-from-file=.env` (see `.vscode/launch.json`).

## Environment Variables
Defined in `lib/core/config/app_config.dart` and supplied via `--dart-define` or `--dart-define-from-file`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `API_BASE_URL` | `http://localhost:8000` | Base URL for `/analyze` |
| `A2A_AGENT_URL` | `http://localhost:8000/a2a` | A2A agent endpoint |
| `ENVIRONMENT` | `development` | App environment label |
| `DEBUG_MODE` | `false` | Enables debug features |

## API
- OpenAPI spec: `api_spec.yaml`
- Analysis endpoint: `POST /analyze` (SSE stream)

## Localization (i18n)
- ARB files in `lib/l10n/`
- Generate localization files:
  ```bash
  flutter gen-l10n
  ```

## Code Generation
This project uses `build_runner` for generated models/adapters.

```bash
dart run build_runner build --delete-conflicting-outputs
```

## Testing & Linting
```bash
flutter test
flutter analyze
```

## Build & Deploy
Production builds and deployment use the Makefile and `.env.prod`.

```bash
make build   # flutter build web --dart-define-from-file=.env.prod
make deploy  # firebase deploy --only hosting
make prod    # build + deploy
make clean   # flutter clean
```

## PWA Notes
- PWA manifest/service worker integration is tracked as pending work.
- Web persistence uses Hive (IndexedDB under the hood).

## Design & Accessibility Principles
- Deep Space palette optimized for OLED (`#000000` background)
- High contrast text and large touch targets (48x48dp minimum)
- Semantic labels and system font scaling
- Graceful degradation for web camera/manual controls

## Pending Work
- Camera package integration for Observatory
- PWA manifest + service worker
- Widget and integration tests
- Accessibility audit

## Contributing
1. Create a feature branch.
2. Ensure `flutter analyze` and `flutter test` pass.
3. Keep UI aligned with the Deep Space theme and accessibility guidelines.

## License
No license file is present. Treat this repository as proprietary unless a license is added.
