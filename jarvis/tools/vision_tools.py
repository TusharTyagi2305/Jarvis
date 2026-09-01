from typing import Dict, Any
import pyautogui
from jarvis.tools.base import BaseTool, ToolResult, Tuple_Validation
from jarvis.security.permissions import RiskLevel
from jarvis.vision.analyzer import screen_analyzer

class ScreenCaptureTool(BaseTool):
    name = "screen_capture"
    description = "Captures full Windows desktop screenshot and returns image file path."
    risk_level = RiskLevel.SAFE
    parameters = {"type": "OBJECT", "properties": {}, "required": []}

    def execute(self, **kwargs: Any) -> ToolResult:
        img, file_path, title = screen_analyzer.capture.capture_screen()
        return ToolResult(success=True, data={"screenshot_path": file_path, "active_window": title})


class ScreenAnalyzeTool(BaseTool):
    name = "screen_analyze"
    description = "Captures and analyzes current desktop screenshot, returning a structured summary of visible windows, text, errors, and UI elements."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "prompt": {
                "type": "STRING",
                "description": "Optional prompt/question to focus the visual analysis on (e.g. 'What error is visible?')."
            }
        },
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        prompt = kwargs.get("prompt")
        analysis = screen_analyzer.analyze_screen(prompt=prompt, force_refresh=True)
        return ToolResult(success=True, data=analysis.model_dump())


class ScreenFindElementTool(BaseTool):
    name = "screen_find_element"
    description = "Locates a specific visual element or button on the desktop screen by text/label (e.g. 'Run button', 'Submit', icons) using screen analysis."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "target": {
                "type": "STRING",
                "description": "Target element label or description (e.g. 'Run button', 'Search input')."
            }
        },
        "required": ["target"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        t = kwargs.get("target")
        if not t or not isinstance(t, str):
            return Tuple_Validation(is_valid=False, error="target must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        element = screen_analyzer.find_element(kwargs["target"])
        if element:
            return ToolResult(success=True, data=element.model_dump())
        else:
            return ToolResult(success=False, error=f"Unable to locate element '{kwargs['target']}' on screen.")


class ScreenClickTool(BaseTool):
    name = "screen_click"
    description = "Locates target element visually on screen, clicks it, and verifies state change (Observe-Act-Verify loop)."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "target": {
                "type": "STRING",
                "description": "Target element description to click."
            }
        },
        "required": ["target"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        t = kwargs.get("target")
        if not t or not isinstance(t, str):
            return Tuple_Validation(is_valid=False, error="target must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        res = screen_analyzer.visual_click(kwargs["target"])
        return ToolResult(success=res.get("success", False), data=res, error=res.get("error"))


class ScreenTypeTool(BaseTool):
    name = "screen_type"
    description = "Locates an input field visually, focuses it, and types text."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "target": {
                "type": "STRING",
                "description": "Input field description."
            },
            "text": {
                "type": "STRING",
                "description": "Text to type."
            }
        },
        "required": ["target", "text"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        t = kwargs.get("target")
        txt = kwargs.get("text")
        if not t or not isinstance(t, str):
            return Tuple_Validation(is_valid=False, error="target must be a non-empty string.")
        if txt is None or not isinstance(txt, str):
            return Tuple_Validation(is_valid=False, error="text must be a string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        res = screen_analyzer.visual_type(kwargs["target"], kwargs["text"])
        return ToolResult(success=res.get("success", False), data=res, error=res.get("error"))


class ScreenPressKeyTool(BaseTool):
    name = "screen_press_key"
    description = "Sends a keyboard key press (e.g. 'enter', 'tab', 'escape', 'f5') to active screen."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "key": {
                "type": "STRING",
                "description": "Key name to press."
            }
        },
        "required": ["key"]
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        key = kwargs.get("key", "enter").lower()
        try:
            pyautogui.press(key)
        except Exception:
            pass
        return ToolResult(success=True, data={"key": key})
