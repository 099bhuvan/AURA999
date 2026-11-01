# ◈ AURA — Pure Python AI Personal Assistant

> **A real, advanced, futuristic, JARVIS-inspired desktop personal AI assistant built exclusively in Python.**

![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg)
![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt%206)-00f0ff.svg)
![Architecture](https://img.shields.io/badge/Architecture-Modular%20Async%20Workers-8a2be2.svg)
![AI Providers](https://img.shields.io/badge/AI-Ollama%20(Offline)%20%7C%20OpenAI--Compatible%20(Online)-00ff9d.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-blue.svg)

---

## 1. Project Overview

**AURA** is a cinematic, command-center personal desktop assistant engineered in pure Python. It combines local and cloud neural intelligence, real-time voice synthesis and recognition, persistent long-term memory, document analysis, background reminder scheduling, and strictly sandboxed Windows automation into a unified, responsive Qt desktop application.

### Strict Pure-Python Architecture:
- **No Web Technologies**: Zero HTML/CSS/JavaScript frameworks, zero React, zero Electron, zero Node.js.
- **QML-Free PySide6**: Built with native Python widgets, custom `QPainter` drawing pipelines, and `QTimer` animation rendering.
- **Thread Safety**: Long-running network queries, audio recording, speech synthesis, and AI inference run isolated on dedicated `QThread` workers, guaranteeing a smooth 60 FPS user experience.

---

## 2. Cinematic Visual Identity

Inspired by cinematic AI command centers, AURA features:
- **Deep Navy & Obsidian Backgrounds**: `#04060a` and `#070b14` for immersive high-contrast readability.
- **Electric Cyan & Blue Accents**: `#00f0ff` luminous glows and `#0072ff` energy gradients.
- **Subtle Violet Accents**: `#8a2be2` indicator highlights.
- **Custom-Painted Glass Panels**: Translucent panels with neon border ticks and soft gradients.
- **Interactive Animated AURA Core**:
  - Concentric reticle rings with rotating tick marks.
  - Glowing multi-layered central sphere and highlight bead.
  - Orbiting nodes and harmonic acoustic waveforms.
  - Floating energy particles with reduced-motion mode support.
  - **Dynamic State Engine**:
    - `IDLE`: Calm breathing pulse and smooth orbital rotation.
    - `LISTENING`: Real-time reactive audio waveform expanding to your voice.
    - `THINKING`: High-speed violet orbital rotation and pulsing energy field.
    - `SPEAKING`: Harmonic acoustic resonance rings synchronized with TTS playback.
    - `ERROR`: Crimson emergency reticle and warning pulse.
  - **Mouse Interactive**: Drag horizontally across the core to rotate its visual field with momentum.

---

## 3. Core Modules & Capabilities

```
AURA Core Architecture
┌────────────────────────────────────────────────────────┐
│               PySide6 Desktop Interface               │
│  [Home] [Chat] [Voice] [Memory] [Docs] [Remind] [Auto] │
└──────────────────────────┬─────────────────────────────┘
                           │ Signals / Slots
┌──────────────────────────▼─────────────────────────────┐
│                 Asynchronous Workers                   │
│      AIWorker (QThread)  │  VoiceWorker (QThread)      │
└──────────────┬───────────────────────────┬─────────────┘
               │                           │
┌──────────────▼────────────┐ ┌────────────▼─────────────┐
│       Core Services       │ │       Storage Layer      │
│ • AI Provider Routing     │ │ • SQLite 3 (aura.db)     │
│   - Offline Ollama        │ │ • Schema Migrations      │
│   - Online Compatible API │ │ • Conversations/Messages │
│ • Voice & TTS Engine      │ │ • Long-Term Memory Bank  │
│ • Document Intelligence   │ │ • Document Metadata      │
│ • Smart Reminders (APS)   │ │ • Scheduled Reminders    │
│ • Controlled Automation   │ │ • Automation Audit Trail │
└───────────────────────────┘ └──────────────────────────┘
```

### 1. Home Dashboard
Real-time telemetry, customizable assistant greeting, animated AURA core widget, quick system status chips (CPU/RAM, audio, provider), quick action buttons, and live previews of upcoming reminders and recent conversations.

### 2. AI Neural Chat
- Multi-session chat history stored in local SQLite database.
- Real-time response streaming with live token generation.
- Session management: create, rename, and delete conversations.
- One-click response copy to clipboard.
- Response cancellation in progress.
- Context injection of verified user memories and ingested document text.
- Safe Markdown and inline code rendering.

### 3. Voice Assistant
- Microphone audio capture powered by `sounddevice` with live RMS audio waveform reactivity.
- Speech-to-Text transcription via `SpeechRecognition`.
- Offline Text-to-Speech synthesis using `pyttsx3` (Windows SAPI5 engine).
- Adjustable speech rate (words per minute) and master volume sliders.
- Text-only fallback console for devices without microphone hardware.

### 4. Online and Offline AI Routing
- **Offline Mode**: Direct HTTP integration with local Ollama (`http://localhost:11434`) using models such as `llama3.2` or `mistral`. Zero cloud transmission.
- **Online Mode**: High-performance HTTP client (`httpx`) connecting to standard OpenAI-compatible endpoints (`/v1/chat/completions`). Supports OpenAI, Groq, OpenRouter, Together, or Gemini endpoints.
- **Automatic Mode**: Automatically tests local Ollama first. If Ollama is offline or unavailable, seamlessly routes to configured online AI with an alert notification.

### 5. Long-Term Memory
- Save and organize verified user preferences, facts, and custom rules in SQLite.
- Keyword and semantic token retrieval to automatically enrich AI prompts with context.
- Dedicated UI to search, edit, delete, or wipe memories with explicit user confirmation.

### 6. Document Intelligence
- Local file text extraction supporting **PDF** (`PyMuPDF`), **DOCX** (`python-docx`), and **TXT** / **MD**.
- Automatic executive summaries and actionable key takeaway extraction.
- Grounded Q&A: Ingest documents and interrogate them with AI models.
- Security protection: document text is isolated as untrusted data in prompts to prevent prompt injection.

### 7. Smart Reminders
- Background scheduling powered by `APScheduler`.
- Startup recovery: automatically checks and flags tasks that became overdue while AURA was closed.
- Categorized views: Upcoming, Overdue, and Completed History.
- Windows audible alert sound and interactive notifications.

### 8. Controlled Desktop Automation
- **Strict Allowlist**: Only explicit, pre-approved actions can execute:
  - `open_application`: Launch approved Windows apps (`notepad`, `calc`, `explorer`, `paint`, `taskmgr`).
  - `open_website`: Open validated `http://` or `https://` URLs in default browser.
  - `create_note`: Save text notes in AURA's local notes folder.
  - `system_info`: Inspect CPU, memory, storage, boot time, and OS diagnostics.
  - `find_files`: Locate files matching safe patterns in user documents.
  - `lock_workstation`: Safely lock the workstation.
- **Security Guardrails**:
  - Never runs arbitrary AI-generated shell/cmd/PowerShell scripts.
  - Explicit user confirmation required for file modifications or workstation locking.
  - Immutable audit trail recorded in SQLite `automation_audit`.
  - Prominent **Emergency Stop Button**: trips safety circuit and immediately rejects all automation actions.

### 9. Custom Assistant Name
- Rename the assistant anytime in Settings (e.g. `JARVIS`, `FRIDAY`, `AURA`).
- Instantly updates application titles, header badges, dynamic greetings, and AI system prompts.

---

## 4. Installation & Windows Setup Guide

### Step 1: Clone or Open the Project
Ensure you are in the project folder:
```powershell
cd c:\Users\Admin\Desktop\AURA
```

### Step 2: Create a Python Virtual Environment
Using Python 3.12:
```powershell
python -m venv .venv
```
Activate the environment:
```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (Optional)
Copy the example environment template:
```powershell
Copy-Item .env.example .env
```
Edit `.env` to configure your online API key or preferred default AI mode:
```env
AURA_ASSISTANT_NAME=AURA
AI_DEFAULT_MODE=automatic
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
ONLINE_API_KEY=your_api_key_here
ONLINE_API_BASE_URL=https://api.openai.com/v1
ONLINE_MODEL_NAME=gpt-4o-mini
```

---

## 5. Setting Up Local Offline AI (Ollama)

For complete offline privacy without cloud dependencies:

1. Download and install Ollama for Windows from [https://ollama.com](https://ollama.com).
2. Open Windows Terminal and pull a recommended model:
   ```powershell
   ollama run llama3.2
   ```
3. In AURA's **Settings** tab, verify the endpoint is `http://localhost:11434` and click **"Test Ollama Connection"**.
4. Once verified, AURA will generate all responses locally on your GPU/CPU with zero internet required.

---

## 6. Running the Application

### Option A: Via Command Line
```powershell
.\.venv\Scripts\python.exe main.py
```

### Option B: Via Windows Launcher Script
Double-click `run_aura.bat` in the root folder.

---

## 7. Running the Automated Test Suite

AURA includes a comprehensive test suite covering the database, memory engine, reminder scheduler, AI manager, automation allowlist, and PySide6 GUI:

```powershell
.\.venv\Scripts\pytest.exe -v
```

All 28 unit and integration tests run and verify full system stability.

---

## 8. Hosting Online (Render & Hugging Face Spaces Cloud Streaming)

AURA can be deployed online using Docker and noVNC/WebRTC cloud streaming on **Render** or **Hugging Face Spaces**. This allows you to interact with the full PySide6 desktop command center directly inside any web browser on desktop, tablet, or phone without installing Python or Qt locally.

### Option 1: Deploy on Render
1. Push the repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), create a **New Web Service** and select your GitHub repo.
3. Render automatically detects the root `Dockerfile`.
4. Set environment variables: `PORT=10000`, `AI_DEFAULT_MODE=online`, and `ONLINE_API_KEY=your_key`.
5. Open your `https://your-app.onrender.com` link to interact with AURA live in your browser!
> 📖 See the full guide in [docs/RENDER_DEPLOYMENT.md](file:///c:/Users/Admin/Desktop/AURA/docs/RENDER_DEPLOYMENT.md).

### Option 2: Deploy on Hugging Face Spaces
1. Create a new Space on [Hugging Face](https://huggingface.co/new-space) using the **Docker (Blank)** template.
2. Push or upload the AURA codebase.
3. In Space **Settings > Variables and secrets**, add your `ONLINE_API_KEY`.
4. AURA will stream live over port `7860` directly in your browser.
> 📖 See the full guide in [docs/HUGGINGFACE_DEPLOYMENT.md](file:///c:/Users/Admin/Desktop/AURA/docs/HUGGINGFACE_DEPLOYMENT.md).

---

## 9. Packaging into a Windows Executable (.exe)

To bundle AURA into a standalone Windows application:

```powershell
.\.venv\Scripts\pyinstaller.exe aura.spec
```

The resulting distribution folder containing `AURA.exe` and its dependencies will be compiled into `dist\AURA\`.

---

## 10. Architecture & Directory Structure

```
AURA/
├── main.py                     # Primary desktop entry point
├── requirements.txt            # Locked modern dependencies
├── aura.spec                   # PyInstaller packaging specification
├── run_aura.bat                # Windows 1-click launcher
├── .env.example                # Configuration template
├── README.md                   # Comprehensive documentation
│
├── app/
│   ├── __init__.py
│   ├── config.py               # Path resolution & settings dataclass
│   │
│   ├── core/                   # Core business logic & services
│   │   ├── __init__.py
│   │   ├── provider_base.py    # Abstract AI provider interface
│   │   ├── ollama_provider.py  # Local offline Ollama HTTP client
│   │   ├── online_provider.py  # OpenAI-compatible cloud client
│   │   ├── ai_manager.py       # Intelligent fallback routing & prompts
│   │   ├── memory_service.py   # User long-term memory management
│   │   ├── document_service.py # PyMuPDF & docx text intelligence
│   │   ├── reminder_service.py # APScheduler & alert recovery
│   │   ├── automation_service.py # Sandboxed Windows automation allowlist
│   │   └── voice_service.py    # Sounddevice capture & pyttsx3 TTS
│   │
│   ├── database/               # SQLite persistence layer
│   │   ├── __init__.py
│   │   ├── database.py         # Thread-safe DatabaseService repository
│   │   ├── models.py           # Typed record dataclasses
│   │   └── migrations.py       # Atomic schema migrations
│   │
│   └── ui/                     # PySide6 desktop GUI
│       ├── __init__.py
│       ├── main_window.py      # Main window orchestrator
│       ├── theme.py            # Cyberpunk QSS & color system
│       │
│       ├── widgets/            # Custom reusable widgets
│       │   ├── __init__.py
│       │   ├── aura_core.py    # Interactive animated AURA Core
│       │   ├── glass_panel.py  # Custom-painted glass-morphism panel
│       │   ├── sidebar.py      # Navigation sidebar with status chip
│       │   └── status_widget.py # Top telemetry & emergency stop bar
│       │
│       ├── pages/              # Section views
│       │   ├── __init__.py
│       │   ├── home_page.py    # Command center dashboard
│       │   ├── chat_page.py    # AI chat & conversation history
│       │   ├── voice_page.py   # Push-to-talk voice console
│       │   ├── memory_page.py  # Long-term memory manager
│       │   ├── documents_page.py # Document summarization & Q&A
│       │   ├── reminders_page.py # Scheduled reminders table
│       │   ├── automation_page.py # Controlled desktop automation & audit
│       │   └── settings_page.py # Model configuration & custom name
│       │
│       └── workers/            # Non-blocking QThread workers
│           ├── __init__.py
│           ├── ai_worker.py    # Asynchronous streaming AI worker
│           └── voice_worker.py # Audio recording & TTS workers
│
└── tests/                      # Automated test suite
    ├── __init__.py
    ├── test_database.py        # SQLite migrations & CRUD tests
    ├── test_memory.py          # Long-term memory search & scoring tests
    ├── test_reminders.py       # Scheduler & startup recovery tests
    ├── test_ai_manager.py      # Provider routing & prompt injection tests
    ├── test_automation.py      # Allowlist & emergency stop tests
    ├── test_document_service.py# PDF/DOCX/TXT extraction tests
    └── test_gui.py             # Offscreen PySide6 GUI tests
```

---

## 10. Security & Privacy Guarantees

1. **Local-First Storage**: All conversations, memories, reminders, documents, and audit logs are stored exclusively in your local SQLite database at `%LOCALAPPDATA%\AURA\aura.db`.
2. **Zero Unapproved Data Transmission**: In Offline mode, no data leaves your workstation. In Automatic mode, AURA notifies you prior to cloud fallback.
3. **No Arbitrary Code Execution**: AURA enforces a strict, hardcoded action allowlist for desktop automation. It will never run arbitrary AI-generated terminal commands or scripts.
4. **Transparent Audit Trail**: Every automated action executed, denied, or failed is logged with timestamps and parameters in the database.
5. **No Hidden Audio Capture**: The microphone is accessed strictly when the user initiates recording and is completely released upon completion.
