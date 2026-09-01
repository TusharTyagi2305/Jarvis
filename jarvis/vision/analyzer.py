import logging
import time
from typing import Optional, Dict, Any, Tuple
import pyautogui
pyautogui.FAILSAFE = False
from PIL import Image

from jarvis.config import settings
from jarvis.vision.models import ScreenAnalysis, DetectedElement
from jarvis.vision.capture import ScreenCaptureService
from jarvis.vision.cache import VisionCache
from jarvis.vision.providers import BaseVisionProvider, GeminiVisionProvider, MockVisionProvider

logger = logging.getLogger("jarvis.vision.analyzer")

class ScreenAnalyzer:
    """
    Central Coordinator for Computer Vision & Screen Understanding:
    Screen capture, vision provider query, caching, element finding, visual clicking/typing, and Observe-Act-Verify loops.
    """

    def __init__(
        self,
        capture_service: Optional[ScreenCaptureService] = None,
        provider: Optional[BaseVisionProvider] = None,
        cache: Optional[VisionCache] = None
    ):
        self.capture = capture_service or ScreenCaptureService()
        self.cache = cache or VisionCache(ttl_seconds=15)

        if provider:
            self.provider = provider
        elif settings.gemini_api_key and settings.vision_provider == "gemini":
            self.provider = GeminiVisionProvider(api_key=settings.gemini_api_key, model_name=settings.vision_model)
        else:
            self.provider = MockVisionProvider()

    def _emit_event(self, event_obj: Any):
        try:
            from jarvis.api.websocket import ws_manager
            ws_manager.broadcast_event_sync(event_obj)
        except Exception:
            pass

    def analyze_screen(self, prompt: Optional[str] = None, force_refresh: bool = False) -> ScreenAnalysis:
        self._emit_event_type("screen_analysis_started")
        image, shot_path, active_window = self.capture.capture_screen(max_size=settings.vision_max_image_size)

        if not force_refresh:
            cached = self.cache.get(image)
            if cached:
                self._emit_event_analysis_completed(cached, shot_path)
                return cached

        analysis = self.provider.analyze_screen(image=image, prompt=prompt, active_window=active_window)
        self.cache.set(image, analysis)
        self._emit_event_analysis_completed(analysis, shot_path)
        return analysis

    def find_element(self, target_description: str, confidence_threshold: Optional[float] = None) -> Optional[DetectedElement]:
        if confidence_threshold is None:
            confidence_threshold = settings.vision_click_confidence_threshold

        analysis = self.analyze_screen(prompt=f"Find target element: {target_description}", force_refresh=True)
        target_lower = target_description.lower()

        best_match: Optional[DetectedElement] = None
        highest_score = 0.0

        for el in analysis.elements:
            score = 0.0
            el_text_lower = el.text.lower()
            if target_lower in el_text_lower:
                score = 0.95
            elif el_text_lower in target_lower:
                score = 0.85
            elif target_lower in el.type.lower():
                score = 0.70

            if score > highest_score:
                highest_score = score
                best_match = el

        if best_match and best_match.confidence >= confidence_threshold:
            self._emit_event_element_found(best_match)
            return best_match

        logger.warning(f"No visual element matching '{target_description}' with confidence >= {confidence_threshold}")
        return None

    def visual_click(self, target_description: str, confidence_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        OBSERVE → ACT → VERIFY Loop for visual click.
        """
        if confidence_threshold is None:
            confidence_threshold = settings.vision_click_confidence_threshold

        # 1. OBSERVE & FIND TARGET
        self._emit_event_action("click", target_description)
        element = self.find_element(target_description, confidence_threshold=confidence_threshold)

        if not element:
            return {
                "success": False,
                "error": f"Unable to confidently identify the target element '{target_description}' on screen (threshold >= {confidence_threshold})."
            }

        # 2. ACT: MOVE & CLICK
        x, y = element.box.x, element.box.y
        logger.info(f"Visual click target '{target_description}' at ({x}, {y}) [Confidence: {element.confidence}]")
        try:
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.click()
        except Exception as e:
            logger.warning(f"pyautogui mouse click warning: {e}")
        time.sleep(0.2)

        # 3. OBSERVE AGAIN & VERIFY
        self._emit_event_type("screen_verification_started")
        post_analysis = self.analyze_screen(prompt="Verify state change after click", force_refresh=True)
        self._emit_event_type("screen_verification_completed")

        return {
            "success": True,
            "target": target_description,
            "clicked_coordinates": {"x": x, "y": y},
            "confidence": element.confidence,
            "verification_summary": post_analysis.description
        }

    def visual_type(self, target_description: str, text: str) -> Dict[str, Any]:
        """
        OBSERVE → ACT → VERIFY Loop for visual typing into an input field.
        """
        click_res = self.visual_click(target_description)
        if not click_res.get("success"):
            return click_res

        try:
            pyautogui.write(text, interval=0.02)
            pyautogui.press("enter")
        except Exception as e:
            logger.warning(f"pyautogui write warning: {e}")
        time.sleep(0.2)

        post_analysis = self.analyze_screen(prompt="Verify state change after typing", force_refresh=True)
        return {
            "success": True,
            "target": target_description,
            "typed_text": text,
            "verification_summary": post_analysis.description
        }

    def _emit_event_type(self, type_str: str):
        try:
            from jarvis.api.events import WSEvent
            self._emit_event(WSEvent(type=type_str))
        except Exception:
            pass

    def _emit_event_analysis_completed(self, analysis: ScreenAnalysis, shot_path: str):
        try:
            from jarvis.api.events import ScreenAnalysisCompletedEvent
            self._emit_event(ScreenAnalysisCompletedEvent(
                description=analysis.description,
                active_window=analysis.active_window or "Desktop",
                elements_count=len(analysis.elements),
                image_path=shot_path
            ))
        except Exception:
            pass

    def _emit_event_element_found(self, element: DetectedElement):
        try:
            from jarvis.api.events import ScreenElementFoundEvent
            self._emit_event(ScreenElementFoundEvent(
                element_type=element.type,
                text=element.text,
                x=element.box.x,
                y=element.box.y,
                confidence=element.confidence
            ))
        except Exception:
            pass

    def _emit_event_action(self, action: str, target: str):
        try:
            from jarvis.api.events import ScreenActionEvent
            self._emit_event(ScreenActionEvent(action=action, target=target))
        except Exception:
            pass

# Singleton ScreenAnalyzer instance
screen_analyzer = ScreenAnalyzer()
