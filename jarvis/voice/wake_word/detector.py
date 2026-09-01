import logging
from typing import Optional, Any
from jarvis.voice.base import BaseWakeWordDetector

logger = logging.getLogger("jarvis.voice.wake_word")

class KeywordWakeWordDetector(BaseWakeWordDetector):
    """
    Wake word detector that checks for target keyword in audio streams or transcribed text.
    Default keyword: 'jarvis'
    """

    def __init__(self, keyword: str = "jarvis"):
        self.keyword = keyword.strip().lower()

    def detect(self, audio_chunk: Optional[Any] = None, target_keyword: str = "jarvis") -> bool:
        kw = (target_keyword or self.keyword).lower()
        if not audio_chunk:
            return False
        text_val = str(audio_chunk).lower().strip()
        variations = [kw, f"hey {kw}", f"{kw} please", f"ok {kw}"]
        return any(var in text_val for var in variations)
