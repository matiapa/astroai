# AGENTS.md — AstroGuide Application Documentation

> This document provides comprehensive context for AI agents and developers working on this codebase.

---

## Project Overview

**AstroGuide** is a mobile-first (APK + PWA) Flutter application that transforms nighttime sky viewing into an interactive, educational experience. Users point their device at the sky, capture images, and receive AI-powered analysis with audio narration identifying celestial objects.

### Core Experience Flow
```
Capture → Analyze → Reveal → Converse
   ↓         ↓         ↓         ↓
Camera   API Call   Results   A2A Chat
```

### Target Platforms
- **Android**: Native APK via Flutter
- **Web**: Progressive Web App (PWA) for broader accessibility

---

## Design Principles

### 1. Dark-First UI ("Deep Space" Theme)
The app is designed for **nighttime use in dark environments**. All design decisions prioritize:
- **OLED optimization**: Pure black (`#000000`) backgrounds save battery and reduce eye strain
- **Low-glare accents**: Neon cyan (`#00D4FF`) and space violet (`#7B2FBE`) provide visibility without harsh brightness
- **High contrast text**: White on black with muted secondary colors

### 2. Immersive, Narrative Experience
Rather than a clinical data dump, the app presents discoveries as a **guided journey**:
- Audio narration tells the "story" of what's visible
- Results reveal objects with animated hotspots
- The AI chat maintains a knowledgeable, exploratory tone

### 3. Accessibility First
- Large touch targets (minimum 48x48dp)
- Semantic labels for screen readers
- Support for system font scaling
- High contrast ratios (4.5:1 minimum)

### 4. Graceful Degradation
Features adapt to platform capabilities:
- Camera falls back to gallery upload on web
- Audio features degrade gracefully without microphone
- Offline mode with cached results

---

## Features

| Feature | Screen | Status |
|---------|--------|--------|
| Camera capture with manual controls | Observatory | UI Complete |
| Gallery image upload | Observatory | Complete |
| AI-powered sky analysis | Results | Complete |
| Interactive object hotspots | Results | Complete |
| Audio narration playback | Results | Complete |
| Conversational AI chat (Atlas) | Chat | Complete |
| Discovery history gallery | Logbook | Complete |
| User preferences | Settings | Complete |
| Internationalization | All | Complete (EN/ES) |

---

## Architecture

### Layer Structure
```
lib/
├── main.dart                              # Entry point, Hive init, system UI
├── core/                                  # Shared infrastructure
│   ├── navigation/
│   │   ├── app_router.dart                # GoRouter configuration
│   │   └── responsive_scaffold.dart       # Adaptive navigation scaffold
│   └── theme/
│       └── app_theme.dart                 # Colors, typography, themes
└── features/                              # Feature-based organization
    ├── observatory/
    │   └── screens/
    │       └── observatory_screen.dart    # Camera/capture
    ├── logbook/
    │   ├── models/
    │   │   ├── logbook_entry.dart         # Hive storage model
    │   │   └── logbook_entry.g.dart       # Hive adapter
    │   ├── providers/
    │   │   └── logbook_provider.dart      # State management
    │   ├── screens/
    │   │   └── logbook_screen.dart        # History gallery
    │   └── services/
    │       └── logbook_service.dart       # Local storage service
    ├── results/
    │   ├── models/
    │   │   ├── analysis_result.dart       # API response models
    │   │   └── analysis_result.g.dart     # Generated JSON serializers
    │   ├── screens/
    │   │   └── results_screen.dart        # Analysis display
    │   └── services/
    │       └── analysis_service.dart      # API client for /analyze
    ├── settings/
    │   └── screens/
    │       └── settings_screen.dart       # Preferences
    └── chat/
        ├── providers/
        │   └── a2a_provider.dart          # A2A JSON-RPC bridge (Dio)
        ├── screens/
        │   ├── main_chat_screen.dart      # Main Atlas chat
        │   └── results_chat_screen.dart   # Contextual analysis chat
        └── theme/
            └── chat_theme.dart            # Deep Space chat styles
```

### State Management Strategy
- **Riverpod** for app-wide state (settings, auth, cached data)
- **Local widget state** for ephemeral UI state (form inputs, animations)
- **Hive** for persistent local storage (logbook entries)

### Navigation
- **GoRouter** handles all routing including deep links
- **ShellRoute** wraps main screens with responsive navigation
- Routes: `/observatory`, `/logbook`, `/chat`, `/settings`, `/results/:id`, `/chat/:id`

### Responsive Navigation
```dart
// Breakpoint: 600px
< 600px  → BottomNavigationBar (mobile)
≥ 600px  → NavigationRail (tablet/desktop)
```

---

## Key Technical Decisions

### Why GoRouter over Navigator 2.0 directly?
GoRouter provides declarative routing with deep link support out of the box, essential for PWA URLs and potential widget/shortcut integration on Android.

### Why Riverpod over BLoC or GetX?
User rules specified native-first state management. Riverpod offers type-safe, testable state with minimal boilerplate while following Flutter team recommendations.

### Why Hive over SQLite?
Hive is lightweight, pure Dart (no native dependencies), and perfect for the simple key-value storage needs of the logbook. It also works seamlessly on web.

### Why google_fonts over bundled fonts?
Reduces app bundle size significantly. Fonts are cached on first load and work seamlessly across platforms. JetBrains Mono and Inter are loaded dynamically.

### Internationalization (i18n)
The app supports multiple languages (currently English and Spanish) using Flutter's native `flutter_localizations` and `intl` package.
- **Source**: `lib/l10n/*.arb` files (Application Resource Bundles).
- **Generation**: `flutter gen-l10n` generates type-safe Dart code in `lib/l10n/generated/`.
- **Usage**: `AppLocalizations.of(context)!.keyName`.
- **Verification**: Ensure no hardcoded strings exist in UI widgets.

### Why A2A protocol for chat?
The A2A (Agent-to-Agent) protocol provides a standardized way for the Flutter app to communicate with a backend AI agent, supporting:
- Multimodal messages (text, images, audio)
- Streaming responses
- Task-based conversation management
- Built-in artifact handling

### Why direct JSON-RPC calls for A2A on web?
The web build rejects streaming request bodies without `duplex: "half"`, which the `a2a` package's HTTP layer doesn't set. The app uses Dio to send standard JSON-RPC POSTs while still leveraging A2A models for parsing.

---

## Color Palette Reference

| Name | Hex | Usage |
|------|-----|-------|
| Background | `#000000` | Primary background (OLED black) |
| Surface | `#0A0A0F` | Cards, modals |
| Surface Elevated | `#12121A` | Elevated components |
| Cyan Accent | `#00D4FF` | Primary accent, interactive |
| Violet Accent | `#7B2FBE` | Secondary accent, gradients |
| Success | `#00FF88` | Positive states |
| Warning | `#FFB800` | Caution states |
| Error | `#FF3366` | Error states |
| Text Primary | `#FFFFFF` | Main text |
| Text Secondary | `#B0B0B0` | Supporting text |
| Text Muted | `#606060` | Disabled/hint text |

---

## API Contracts

### Analyze Endpoint

**Endpoint:** `POST /analyze`  
**Content-Type:** `multipart/form-data`  
**Response:** Server-Sent Events (SSE) stream

```bash
curl --location 'http://localhost:8000/analyze' \
  --form 'image=@"/path/to/sky_image.png"' \
  -H 'Accept: text/event-stream'
```

**SSE Event Sequence:**
```
event: analyzing_image     → Progress indicator
event: analysis_complete   → Partial result (plate_solving, identified_objects)
event: generating_narration → Progress indicator
event: narration_complete  → Partial result (title, text, object_legends)
event: generating_audio    → Progress indicator  
event: audio_complete      → Final result (audio_url)
```

The frontend navigates to results screen on `narration_complete`, showing an audio loading indicator until `audio_complete` arrives.

**Response Schema (combined from all events):**
```json
{
  "success": boolean,
  "plate_solving": {
    "center_ra_deg": number,      // Right ascension in degrees
    "center_dec_deg": number,     // Declination in degrees
    "pixel_scale_arcsec": number  // Arcseconds per pixel
  },
  "narration": {
    "title": string,              // Spanish title for the view
    "text": string,               // Full narration text (Spanish)
    "audio_url": string | null    // URL to WAV audio file (null until audio_complete)
  },
  "identified_objects": [
    {
      "name": string,                    // Catalog name
      "type": string,                    // "Star", "Galaxy", "Nebula", etc.
      "subtype": string,                 // "Y*O", "Pulsating Variable", etc.
      "magnitude_visual": number | null, // Apparent magnitude
      "bv_color_index": number | null,   // B-V color index
      "spectral_type": string,           // "M3.2", "A5IV", "B3/5V", etc.
      "morphological_type": string | null,
      "distance_lightyears": number | null,
      "alternative_names": string | null,
      "celestial_coords": {
        "ra_deg": number,                // Right ascension
        "dec_deg": number,               // Declination
        "radius_arcsec": number          // Object radius in arcsec
      },
      "pixel_coords": {
        "x": number,                     // X position in image
        "y": number,                     // Y position in image
        "radius_pixels": number          // Display radius
      },
      "legend": string | null            // Brief description (Spanish)
    }
  ],
  "error": string | null
}
```

**Object Types:**
- `Star` — Regular stars, includes subtypes like Y*O (Young Stellar Object), Pulsating Variable, Orion Variable
- `Galaxy` — Galaxies with morphological_type (e.g., "Sb", "E0")
- `Nebula` — Emission/reflection nebulae
- `Cluster` — Star clusters

### A2A Chat
Atlas chat is implemented with Flutter AI Toolkit's `LlmChatView`, backed by an A2A JSON-RPC provider. The agent URL is configured via `A2A_AGENT_URL` (set with `--dart-define=A2A_AGENT_URL=http://localhost:8000/a2a`).

**Session Management:**
- **contextId**: Groups related tasks within a conversation. Sent with every message so the server keeps tasks associated.
- **taskId**: Identifies individual task sessions. Tasks are marked as "finished" when they complete, after which new messages create a new task within the same context.
- **taskIds**: The `ChatSession` model accumulates every task ID created during a conversation. This list (stored oldest-first) allows reconstructing the full visual history across task boundaries.
- **History Restoration**: When reopening a historical conversation, the app calls `tasks/get` for each stored task ID and merges their message histories in order. New messages are sent with only the `contextId` (not `taskId`) so the server creates a fresh task rather than rejecting a finished one.

---

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Screens | `*_screen.dart` | `observatory_screen.dart` |
| Widgets | `*_widget.dart` or descriptive | `viewfinder_overlay.dart` |
| Providers | `*_provider.dart` | `settings_provider.dart` |
| Models | `*.dart` (noun) | `discovery.dart` |
| Services | `*_service.dart` | `analysis_service.dart` |

---

## Running the Application

```bash
# Install dependencies
flutter pub get

# Run on Chrome (web)
flutter run -d chrome

# Run on Android emulator
flutter run -d emulator-5554

# Build for web
flutter build web

# Build APK
flutter build apk

## Deployment & Production Build

For production deployment, use the provided `Makefile` which handles environment variables using `.env.prod`.

### Prerequisites
1.  Configure `API_BASE_URL` in `.env.prod`.
2.  Ensure you have the Firebase CLI installed and logged in.

### Commands
```bash
# Build for production (Web)
make build

# Deploy to Firebase Hosting
make deploy

# Build and Deploy in one step
make prod

# Clean build artifacts
make clean
```
```

---

## Pending Work

1. **Camera Integration**: Connect `camera` package to Observatory screen
2. **PWA Config**: Add manifest.json and service worker
3. **Testing**: Widget tests, integration tests
4. **Accessibility Audit**: Screen reader, contrast verification

---

## Related Documentation

- [Flutter AI Toolkit](https://pub.dev/packages/flutter_ai_toolkit)
- [A2A Protocol Specification](https://google.github.io/A2A/)
- [GoRouter Documentation](https://pub.dev/packages/go_router)
- [Riverpod Documentation](https://riverpod.dev/)
