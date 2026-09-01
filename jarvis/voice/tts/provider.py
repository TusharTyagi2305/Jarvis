import logging
import threading
from typing import Optional
from jarvis.voice.base import BaseTTSProvider

logger = logging.getLogger("jarvis.voice.tts")

class NativeTTSProvider(BaseTTSProvider):
    """
    TTS Provider using pyttsx3 or SAPI5 engine for speech synthesis.
    Manages speech queue and cancellation without blocking the main event loop.
    """

    def __init__(self, rate: int = 175, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self.is_speaking = False
        self._engine = None
        self._lock = threading.Lock()

        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self.volume)
        except Exception as e:
            logger.warning(f"pyttsx3 engine initialization warning: {e}")
            self._engine = None

    def speak(self, text: str, voice: Optional[str] = None, rate: Optional[int] = None) -> bool:
        if not text or not text.strip():
            return False

        def _worker():
            with self._lock:
                self.is_speaking = True
                try:
                    if self._engine:
                        if rate:
                            self._engine.setProperty("rate", rate)
                        self._engine.say(text)
                        self._engine.runAndWait()
                    else:
                        logger.info(f"[NATIVE TTS SILENT SPEAK]: '{text}'")
                except Exception as e:
                    logger.warning(f"TTS speech output warning: {e}")
                finally:
                    self.is_speaking = False

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return True

    def cancel(self) -> None:
        with self._lock:
            if self._engine and self.is_speaking:
                try:
                    self._engine.stop()
                except Exception as e:
                    logger.warning(f"Error stopping TTS playback: {e}")
            self.is_speaking = False


class MockTTSProvider(BaseTTSProvider):
    """
    Mock TTS Provider for automated tests and silent execution.
    """

    def __init__(self):
        self.spoken_history = []
        self.is_speaking = False

    def speak(self, text: str, voice: Optional[str] = None, rate: Optional[int] = None) -> bool:
        self.spoken_history.append(text)
        logger.info(f"[MOCK TTS SPOKE]: '{text}'")
        return True

    def cancel(self) -> None:
        self.is_speaking = False
