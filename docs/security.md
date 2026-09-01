# JARVIS Security Model

JARVIS follows a Privacy-First & Local-First security design.

1. **Local Network Binding**: FastAPI server binds strictly to `127.0.0.1`.
2. **Permission Engine**: Operations classified as `CONFIRM` or `DANGEROUS` require user confirmation token verification.
3. **Terminal Safety Classifier**: Destructive shell commands (`rm`, `del`, `format`) are blocked or require confirmation.
4. **Sensitive Data Filter**: Automatically detects and blocks passwords, tokens, API keys, and credit cards from permanent memory persistence.
5. **Temporary File Privacy**: Screenshots and temporary audio files are stored in local scratch storage and automatically cleaned up.
