import time
from typing import List, Optional
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x: int = Field(description="Center X pixel coordinate on screen.")
    y: int = Field(description="Center Y pixel coordinate on screen.")
    width: int = Field(default=0, description="Element width in pixels.")
    height: int = Field(default=0, description="Element height in pixels.")

class DetectedElement(BaseModel):
    type: str = Field(description="Element type e.g. button, text, link, input, window, dialog, error.")
    text: str = Field(description="Visible text or label on the element.")
    box: BoundingBox = Field(description="Bounding box coordinates.")
    confidence: float = Field(default=0.9, description="Confidence score between 0.0 and 1.0.")

class ScreenAnalysis(BaseModel):
    description: str = Field(description="High-level description of what is currently visible on the screen.")
    active_window: Optional[str] = Field(default=None, description="Title of the active foreground window.")
    elements: List[DetectedElement] = Field(default_factory=list, description="List of detected UI elements.")
    screenshot_id: str = Field(default_factory=lambda: f"shot_{int(time.time()*1000)}")
    timestamp: float = Field(default_factory=time.time)
