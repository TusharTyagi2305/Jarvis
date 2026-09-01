from abc import ABC, abstractmethod
from typing import Optional
from PIL import Image
from jarvis.vision.models import ScreenAnalysis

class BaseVisionProvider(ABC):
    """
    Abstract interface for multimodal vision providers.
    """

    @abstractmethod
    def analyze_screen(
        self,
        image: Image.Image,
        prompt: Optional[str] = None,
        active_window: Optional[str] = None
    ) -> ScreenAnalysis:
        """
        Analyzes screenshot image and returns normalized ScreenAnalysis.
        """
        pass
