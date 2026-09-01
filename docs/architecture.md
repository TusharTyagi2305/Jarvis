# JARVIS Architecture

JARVIS is built as a single-agent, modular desktop AI assistant for Windows.

## System Topology
```
User (Voice / Web UI / CLI)
          │
          ▼
   JARVIS Launcher (PID Locking & Process Lifecycle)
          │
          ├── FastAPI Service (127.0.0.1:8000)
          │     ├── JarvisOrchestrator (Single Central Agent)
          │     ├── TaskPlanEngine (Graph Dependencies & Retries)
          │     ├── VoiceManager (Wake Word + STT + TTS)
          │     ├── BrowserManager (Playwright Automation)
          │     ├── ScreenAnalyzer (Multimodal Vision)
          │     ├── MemoryManager (SQLite + Semantic Vector)
          │     └── ToolRegistry (35+ Registered Tools)
          │
          └── React HUD Dashboard (Vite + TypeScript)
```

## Security Model
All tool calls pass through `PermissionEngine`. High risk actions require explicit user confirmation token approval.
