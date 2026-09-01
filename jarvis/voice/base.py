import enum
from abc import ABC, abstractmethod
from typing import Optional, Any
from pydantic import BaseModel, Field

class MicState(str, enum.Enum):
    IDLE = "IDLE"
    DISABLED = "DISABLED"
    PERMISSION_REQUIRED = "PERMISSION_REQUIRED"
    WAKE_LISTENING = "WAKE_LISTENING"
    WAKE_DETECTED = "WAKE_DETECTED"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"

class Transcript(BaseModel):
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = "en-IN"
    duration_seconds: Optional[float] = None
    is_final: bool = True

class BaseSTTProvider(ABC):
    """
    Abstract interface for Speech-to-Text providers.
    """

    @abstractmethod
    def transcribe(self, audio_data: Optional[Any] = None, language: str = "en-IN") -> Transcript:
        """
        Transcribes speech audio data to a Transcript.
        """
        pass

class BaseTTSProvider(ABC):
    """
    Abstract interface for Text-to-Speech providers.
    """

    @abstractmethod
    def speak(self, text: str, voice: Optional[str] = None, rate: Optional[int] = None) -> bool:
        """
        Synthesizes and plays speech for the provided text.
        """
        pass

    @abstractmethod
    def cancel(self) -> None:
        """
        Cancels active speech playback.
        """
        pass

class BaseWakeWordDetector(ABC):
    """
    Abstract interface for Wake Word detectors.
    """

    @abstractmethod
    def detect(self, audio_chunk: Optional[Any] = None, target_keyword: str = "jarvis") -> bool:
        """
        Detects if the target wake word keyword was spoken in the audio stream.
        """
        pass
