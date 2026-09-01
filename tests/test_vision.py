import pytest
from PIL import Image
from jarvis.vision.models import BoundingBox, DetectedElement, ScreenAnalysis
from jarvis.vision.capture import ScreenCaptureService
from jarvis.vision.cache import VisionCache
from jarvis.vision.providers.mock import MockVisionProvider
from jarvis.vision.analyzer import ScreenAnalyzer
from jarvis.tools.vision_tools import (
    ScreenCaptureTool,
    ScreenAnalyzeTool,
    ScreenFindElementTool,
    ScreenClickTool,
    ScreenTypeTool
)
from jarvis.security.permissions import RiskLevel

def test_vision_models():
    box = BoundingBox(x=500, y=300, width=100, height=40)
    el = DetectedElement(type="button", text="Submit", box=box, confidence=0.92)
    analysis = ScreenAnalysis(description="Test Screen", active_window="Test App", elements=[el])

    assert analysis.description == "Test Screen"
    assert len(analysis.elements) == 1
    assert analysis.elements[0].box.x == 500

def test_screen_capture_service(tmp_path):
    capture = ScreenCaptureService(temp_dir=tmp_path)
    img, path_str, active_title = capture.capture_screen()
    assert img is not None
    assert active_title != ""

def test_vision_cache():
    cache = VisionCache(ttl_seconds=10)
    img = Image.new("RGB", (100, 100), color="blue")
    analysis = ScreenAnalysis(description="Cached", elements=[])

    assert cache.get(img) is None
    cache.set(img, analysis)
    assert cache.get(img) is not None
    assert cache.get(img).description == "Cached"

def test_screen_analyzer_find_and_confidence():
    provider = MockVisionProvider(preset_elements=[
        DetectedElement(
            type="button",
            text="High Confidence Run",
            box=BoundingBox(x=400, y=200, width=80, height=30),
            confidence=0.95
        ),
        DetectedElement(
            type="button",
            text="Low Confidence Target",
            box=BoundingBox(x=100, y=100, width=40, height=20),
            confidence=0.50
        )
    ])

    analyzer = ScreenAnalyzer(provider=provider)

    # Valid match above threshold 0.85
    found_valid = analyzer.find_element("Run", confidence_threshold=0.85)
    assert found_valid is not None
    assert "Run" in found_valid.text

    # Match below threshold 0.85 should return None (Refusal to click)
    found_low = analyzer.find_element("Target", confidence_threshold=0.85)
    assert found_low is None

def test_visual_click_low_confidence_refusal():
    provider = MockVisionProvider(preset_elements=[
        DetectedElement(
            type="button",
            text="Uncertain Button",
            box=BoundingBox(x=200, y=200, width=50, height=20),
            confidence=0.60
        )
    ])
    analyzer = ScreenAnalyzer(provider=provider)
    res = analyzer.visual_click("Uncertain Button", confidence_threshold=0.85)
    assert res["success"] is False
    assert "Unable to confidently identify" in res["error"]

def test_vision_tools_risk_levels():
    assert ScreenCaptureTool().risk_level == RiskLevel.SAFE
    assert ScreenAnalyzeTool().risk_level == RiskLevel.SAFE
    assert ScreenClickTool().risk_level == RiskLevel.SAFE
