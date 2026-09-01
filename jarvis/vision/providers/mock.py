import logging
from typing import Optional, List
from PIL import Image

from jarvis.vision.providers.base import BaseVisionProvider
from jarvis.vision.models import ScreenAnalysis, DetectedElement, BoundingBox

logger = logging.getLogger("jarvis.vision.provider.mock")

class MockVisionProvider(BaseVisionProvider):
    """
    Mock vision provider for automated unit testing and keyless execution.
    """

    def __init__(self, preset_elements: Optional[List[DetectedElement]] = None):
        self.preset_elements = preset_elements

    def analyze_screen(
        self,
        image: Image.Image,
        prompt: Optional[str] = None,
        active_window: Optional[str] = None
    ) -> ScreenAnalysis:
        width, height = image.size

        if self.preset_elements is not None:
            elements = self.preset_elements
        else:
            elements = [
                DetectedElement(
                    type="button",
                    text="Run",
                    box=BoundingBox(x=width // 2, y=height // 3, width=80, height=35),
                    confidence=0.95
                ),
                DetectedElement(
                    type="input",
                    text="Search",
                    box=BoundingBox(x=width // 2, y=height // 2, width=300, height=40),
                    confidence=0.92
                ),
                DetectedElement(
                    type="text",
                    text="Welcome to Windows Desktop",
                    box=BoundingBox(x=width // 4, y=height // 4, width=200, height=20),
                    confidence=0.98
                )
            ]

        desc = f"Mock Screen Analysis: Active window is '{active_window or 'Desktop'}'. Found {len(elements)} visible elements."
        if prompt:
            desc += f" Query: '{prompt}'."

        return ScreenAnalysis(
            description=desc,
            active_window=active_window,
            elements=elements
        )
