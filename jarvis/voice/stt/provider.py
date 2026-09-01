import logging
from typing import Optional, Any
from jarvis.voice.base import BaseSTTProvider, Transcript

logger = logging.getLogger("jarvis.voice.stt")

class NativeSTTProvider(BaseSTTProvider):
    """
    STT Provider using speech_recognition library to capture audio input and perform STT.
    Falls back gracefully if microphone hardware is unavailable.
    """

    def __init__(self):
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
        except ImportError:
            self.recognizer = None
            logger.warning("speech_recognition module unavailable.")

    def transcribe(self, audio_data: Optional[Any] = None, language: str = "en-IN") -> Transcript:
        if not self.recognizer:
            return Transcript(text="", confidence=0.0, language=language)

        import speech_recognition as sr
        try:
            if audio_data is None:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)

            text = self.recognizer.recognize_google(audio_data, language=language)
            return Transcript(text=text, confidence=0.9, language=language)
        except Exception as e:
            logger.warning(f"STT recognition warning/error: {e}")
            return Transcript(text="", confidence=0.0, language=language)


class MockSTTProvider(BaseSTTProvider):
    """
    Mock STT Provider for automated tests and hardware-less environments.
    """

    def __init__(self, preset_transcript: str = "Jarvis, check battery"):
        self.preset_transcript = preset_transcript

    def transcribe(self, audio_data: Optional[Any] = None, language: str = "en-IN") -> Transcript:
        return Transcript(
            text=self.preset_transcript,
            confidence=0.98,
            language=language,
            duration_seconds=2.5
        )
