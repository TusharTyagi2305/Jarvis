# 🤖 JARVIS — Personal AI Desktop Agent

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-cyan?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal?logo=fastapi&logoColor=white)
![Language](https://img.shields.io/badge/Language-Hindi%20%7C%20Hinglish%20%7C%20English-orange)
![License](https://img.shields.io/badge/License-MIT-green)

An Iron-Man-inspired personal desktop AI assistant built with Python, FastAPI, and React for Windows. JARVIS features natural Hindi-first conversational intelligence, autonomous multi-step planning, safe system command execution via a 3-tier permission engine, Google Gemini 2.5 integration, and a futuristic sci-fi Glassmorphism HUD Dashboard with real-time WebSockets.

---

## 🌟 Primary Capabilities

1. **Hindi-First & Natural Conversational Intelligence**:
   - Native support for Hindi (`hi-IN`), Hinglish, and English with automatic language detection (`JARVIS_AUTO_LANGUAGE_DETECTION=true`).
   - Iron-Man style natural responses capped to 1 concise sentence by default (e.g., `"Notepad खोल दिया."`, `"hasmob002 ke results mil gaye."`).
   - Proper noun protection ensuring tech terms (YouTube, VS Code, GitHub, Notepad) remain pristine.

2. **Futuristic HUD React Dashboard**:
   - Central Animated Glowing **ARC Core** (`IDLE`, `LISTENING`, `PROCESSING`, `PLANNING`, `EXECUTING`, `WAITING`, `COMPLETED`, `ERROR` state transitions).
   - Real-Time WebSocket streaming (`/ws`) for live task steps, tool executions, and system events.
   - System Telemetry panel (CPU, RAM, Disk, Battery, OS).
   - Activity Feed for step-by-step tool execution progress.
   - Interactive Chat & Command Console.
   - Confirmation Modal dialog for explicit user permission approvals.

2. **System & Computer Control**:
   - `get_system_info`: Real-time CPU, RAM, Disk, OS, & Battery metrics via `psutil`.
   - `take_screenshot`: Captures high-res screen images to disk.
   - `open_application`: Launches desktop applications (Chrome, VS Code, Notepad, Calc, etc.).
   - `close_application`: Terminates target running processes cleanly.

3. **File System Management**:
   - `read_file`, `create_file`, `create_folder`, `search_files`, `rename_move_file`, `delete_file`.

4. **Safe Terminal Execution**:
   - `terminal_command`: PowerShell/cmd execution sandbox with output capturing and dangerous keyword filtering.

5. **Security & Permission Engine**:
   - 3-Tier Security model (`SAFE`, `CONFIRM`, `DANGEROUS`).

---

## 📁 Directory Structure

```
Jarvis/
├── .env.example              # Template environment file
├── pyproject.toml            # Backend dependencies
├── README.md                 # Project documentation
├── jarvis/
│   ├── config.py             # Strongly typed settings
│   ├── cli.py                # Interactive CLI mode
│   ├── security/             # PermissionEngine & AuditLogger
│   ├── brain/                # Gemini & Mock LLM providers
│   ├── tools/                # Tool Registry & 11 System/File/Terminal tools
│   ├── orchestrator/         # Planner & 14-Step Agent Execution Loop
│   └── api/                  # FastAPI App, REST Routes & WebSocket Manager (/ws)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── src/
│   │   ├── components/       # Header, JarvisCore, Telemetry, ActivityFeed, Chat, Console, ConfirmationModal, SettingsModal
│   │   ├── hooks/            # useWebSocket, useTelemetry
│   │   ├── services/         # REST & WebSocket API client
│   │   ├── pages/            # Dashboard HUD
│   │   ├── index.css         # Dark Sci-Fi HUD aesthetics & animations
│   │   └── App.tsx
└── tests/                    # 16 unit & integration tests (pytest)
```

---

## 🚀 Quick Start Guide

### 1. Backend Setup
Install Python dependencies:
```bash
pip install -e .[dev]
```
Configure `.env` (optional; if omitted, MockLLMProvider runs offline):
```env
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-flash
MAX_AGENT_ITERATIONS=10
```

Start the FastAPI backend server:
```bash
python -m jarvis.api.app
```
*(Backend runs on `http://127.0.0.1:8000` with WebSocket endpoint `ws://127.0.0.1:8000/ws`)*

### 2. Frontend Dashboard Setup
Navigate to the `frontend/` folder and start Vite:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173` to interact with the JARVIS HUD Dashboard!

---

## 🧪 Running Tests

Execute the backend test suite:
```bash
python -m pytest
```

Build the frontend production bundle:
```bash
cd frontend
npm run build
```

---

## 🗺 Roadmap & Progress

- [x] **Phase 1**: Core Modular Architecture, Tool System, Security Engine, Gemini LLM Abstraction, Agent Loop, REST API & CLI.
- [x] **Phase 2**: Futuristic React Dashboard, Circular ARC Core Animations, WebSockets `/ws`, Live Telemetry & Confirmation UI.
- [ ] **Phase 3**: Voice Module (STT, TTS, Wake Word Activation).
- [ ] **Phase 4**: Playwright Browser Agent.
- [ ] **Phase 5**: Computer Vision & Screen Understanding.
- [ ] **Phase 6**: Vector-based Semantic Memory.
