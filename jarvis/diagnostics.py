import sys
import logging
from typing import Dict, Any
from jarvis.config import settings

logger = logging.getLogger("jarvis.diagnostics")

class StartupDiagnostics:
    """
    Evaluates environment readiness and subsystem health for startup diagnostics.
    Does not crash the application if optional subsystems are absent.
    """

    @classmethod
    def check_environment(cls) -> Dict[str, Any]:
        results = {
            "python": True,
            "version": settings.jarvis_version,
            "audio": False,
            "browser": False,
            "vision": False,
            "memory": False,
            "llm": False
        }

        # Check Python
        if sys.version_info >= (3, 10):
            results["python"] = True

        # Check Audio (speech_recognition / pyttsx3)
        try:
            import speech_recognition
            import pyttsx3
            results["audio"] = True
        except ImportError:
            logger.warning("Audio subsystem packages degraded.")

        # Check Playwright
        try:
            import playwright
            results["browser"] = True
        except ImportError:
            logger.warning("Playwright browser automation package absent.")

        # Check Vision (google.genai SDK)
        try:
            import google.genai
            has_key = bool(settings.gemini_api_key and settings.gemini_api_key.strip() and settings.gemini_api_key != "your_gemini_api_key_here")
            results["vision"] = has_key
        except ImportError:
            logger.warning("GenAI Vision package absent.")

        # Check Memory DB directory
        try:
            from jarvis.memory.providers.sqlite import SQLiteMemoryRepository
            repo = SQLiteMemoryRepository(db_path_str=settings.memory_db_path)
            results["memory"] = True
        except Exception:
            logger.warning("Memory database initialization degraded.")

        # Check LLM configuration
        results["llm"] = bool(settings.gemini_api_key or settings.llm_model)

        return results
