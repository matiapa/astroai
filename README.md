<p align="center">
  <img src="https://i.ibb.co/kV5H93cj/banner-en.png" width="100%" alt="AstroAI Logo">
</p>

# AstroAI: Your AI Copilot for the Night Sky

[![Flutter](https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Gemini AI](https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Google ADK](https://img.shields.io/badge/Google_ADK-F4B400?style=for-the-badge&logo=google-cloud&logoColor=white)](https://github.com/google/agent-development-kit)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg?style=for-the-badge)](LICENSE)

**AstroAI** is an intelligent, multi-agent system designed to bridge the gap between human curiosity and the vastness of the cosmos. Inspired by the clear night skies of Neuquén, Argentina, it gives your telescope an "AI brain" to help you identify objects, plan observations, and learn the history of the universe through conversational narration.

---

### 🏆 Gemini Hackathon
This project was proudly presented as part of the **[Gemini Hackathon](https://devpost.com/software/astroai-iw5yuh)**. You can find the full submission details, demo video, and project pitch on **[Devpost](https://devpost.com/software/astroai-iw5yuh)**, or see the demo video on **[Vimeo](https://vimeo.com/1163337413?share=copy&fl=sv&fe=ci)**.

---

## 🌌 Inspiration

Stargazing is magical, but it has a steep learning curve. You see "stars," but you don't always know *what* you are seeing. While tools like Stellarium are powerful, they can be complex for beginners. AstroAI was born from the desire to make the universe understandable and deeply inspiring for everyone, acting as a personal, multimodal companion—a Carl Sagan for your pocket.

## 🚀 Key Features

- **🔭 Real-Time Multimodal Analysis**: Upload an image from your telescope or point your camera at the sky. Atlas doesn't just identify objects; it performs deep analysis combining visual data with astronomical coordinates.
- **🗺️ Smart Observation Planning**: Acting as an expert guide, Atlas checks your equipment, location, and experience to curate the perfect observation session for you.
- **💬 Conversational Astronomy**: atlas is a knowledgeable companion ready to debate astrophysical theories, explain phenomena, or chat about the wonders of the universe in an educational and engaging tone.
- **🎙️ AI-Powered Narration**: High-quality synthesis using Gemini TTS provides an immersive experience, allowing you to listen to the history of the stars without taking your eyes off the eyepiece.

## 🛠️ How It Works

AstroAI operates on a sophisticated multi-agent architecture built with the **Google Agent Development Kit (ADK)**:

1.  **The Root Agent**: Orchestrates interaction and delegates tasks to specialized sub-agents.
2.  **The Planning Agent**: Calculates visibility, searches catalogs (SIMBAD), and maps locations to precise coordinates.
3.  **The Grounding Pipeline**:
    - **Astrometric Calibration**: Plate-solving on private GKE servers for precise mapping.
    - **Deterministic ID**: SIMBAD query for bright point sources.
    - **Generative Deep Sky Analysis**: Gemini 1.5 Pro analyzes fainter structures (nebulae, galaxies).
    - **Narrative Synthesis**: Gemini 1.5 Flash creates a cohesive, inspiring story.

## 💻 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Flutter (Android + PWA), Google Stitch UI |
| **Backend** | FastAPI, Python 3.10+ |
| **AI Models** | Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini TTS |
| **Frameworks** | Google ADK (Agent Development Kit), A2A Protocol |
| **Infrastructure** | Google Cloud Run, GKE, Terraform, Firebase Hosting |

## 📂 Repository Structure

```text
.
├── backend/      # FastAPI service, AI agents, image analysis pipeline
├── frontend/     # Flutter mobile and web application
├── README.md     # Project overview (this file)
└── AGENTS.md     # Technical guidance for AI agents
```

## 🚦 Getting Started

AstroAI is split into two independent services. Please follow the specific setup instructions in each directory:

- [**Backend Setup**](backend/README.md): API documentation, environment variables, and agent configuration.
- [**Frontend Setup**](frontend/README.md): Running the Flutter app (Web/Android) and connecting to the API.

## 🤝 Contributing

We welcome contributions centered around improving the astronomy experience!
1. Create a feature branch.
2. Ensure you follow the linting/testing guides in the `backend/` and `frontend/` READMEs.
3. Submit a PR for review.

## 📜 License

This project is currently proprietary. Refer to [LICENSE](LICENSE) for terms of use (if provided).
