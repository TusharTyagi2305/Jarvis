import json
import logging
from typing import Optional
from PIL import Image

from jarvis.vision.providers.base import BaseVisionProvider
from jarvis.vision.models import ScreenAnalysis, DetectedElement, BoundingBox

logger = logging.getLogger("jarvis.vision.provider.gemini")

class GeminiVisionProvider(BaseVisionProvider):
    """
    Multimodal vision provider using Google Gemini GenAI SDK to analyze desktop screenshots and detect UI elements.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None

        if api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini GenAI client: {e}")

    def analyze_screen(
        self,
        image: Image.Image,
        prompt: Optional[str] = None,
        active_window: Optional[str] = None
    ) -> ScreenAnalysis:
        if not self.client:
            logger.warning("Gemini Vision API client unavailable. Returning fallback ScreenAnalysis.")
            return ScreenAnalysis(
                description=f"Active window: {active_window or 'Desktop'}. Gemini API key not configured.",
                active_window=active_window,
                elements=[]
            )

        width, height = image.size
        system_prompt = f"""
You are an expert computer vision system analyzing a desktop screenshot (Resolution: {width}x{height}).
The active foreground window is: "{active_window or 'Desktop'}".

User Query: "{prompt or 'Analyze the current screen and identify visible UI elements, text, buttons, input fields, and windows.'}"

Output valid JSON matching this schema:
{{
  "description": "High-level summary of what is visible on screen",
  "elements": [
    {{
      "type": "button | input | link | text | window | dialog | error",
      "text": "visible label or text",
      "x": center_x_pixel,
      "y": center_y_pixel,
      "width": width_pixel,
      "height": height_pixel,
      "confidence": float_between_0_and_1
    }}
  ]
}}
"""
        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[image, system_prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )

            res_text = response.text if response else "{}"
            data = json.loads(res_text)

            description = data.get("description", "Screen analysis complete.")
            raw_elements = data.get("elements", [])

            elements = []
            for el in raw_elements:
                try:
                    elements.append(DetectedElement(
                        type=el.get("type", "element"),
                        text=str(el.get("text", "")),
                        box=BoundingBox(
                            x=int(el.get("x", width // 2)),
                            y=int(el.get("y", height // 2)),
                            width=int(el.get("width", 50)),
                            height=int(el.get("height", 30))
                        ),
                        confidence=float(el.get("confidence", 0.9))
                    ))
                except Exception as ex:
                    logger.warning(f"Error parsing element: {ex}")

            return ScreenAnalysis(
                description=description,
                active_window=active_window,
                elements=elements
            )
        except Exception as e:
            logger.error(f"Gemini Vision API call failed: {e}")
            return ScreenAnalysis(
                description=f"Error analyzing screen: {str(e)}",
                active_window=active_window,
                elements=[]
            )
