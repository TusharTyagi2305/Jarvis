# JARVIS Installation Guide

## Requirements
- Windows 10 / 11 64-bit
- Python 3.10+
- Node.js 18+ & npm

## Development Quickstart

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install Playwright browser:
   ```bash
   playwright install chromium
   ```
3. Build Frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```
4. Start JARVIS:
   ```bash
   python -m jarvis.cli start
   ```
