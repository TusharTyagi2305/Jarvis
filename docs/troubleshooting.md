# JARVIS Troubleshooting Guide

## Common Issues

### 1. Backend Port 8000 Already in Use
Run:
```bash
python -m jarvis.cli stop
```
Or check PID lock at `data/scratch/jarvis.pid`.

### 2. Microphone or Speech Recognition Warning
JARVIS falls back gracefully to Text input mode if microphone audio hardware is unavailable.

### 3. Playwright Chromium Missing
Run:
```bash
playwright install chromium
```

### 4. Vision Target Low Confidence (< 0.85)
Ensure screen resolution is 1080p+ and active application window is visible.
