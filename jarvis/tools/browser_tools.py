from typing import Dict, Any
from jarvis.tools.base import BaseTool, ToolResult, Tuple_Validation
from jarvis.security.permissions import RiskLevel
from jarvis.browser.manager import browser_manager

class BrowserOpenTool(BaseTool):
    name = "browser_open"
    description = "Launches or attaches to a Playwright browser session and loads an initial web page."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "url": {
                "type": "STRING",
                "description": "Optional starting URL (default https://www.google.com)."
            }
        },
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        url = kwargs.get("url", "https://www.google.com")
        res = browser_manager.open_browser(url)
        return ToolResult(success=res.get("success", True), data=res, error=res.get("error"))


class BrowserNavigateTool(BaseTool):
    name = "browser_navigate"
    description = "Navigates active web browser page to specified URL (e.g. https://www.youtube.com, https://google.com). Use when opening websites, YouTube, or online services."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "url": {
                "type": "STRING",
                "description": "Target website URL to navigate to."
            }
        },
        "required": ["url"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        url = kwargs.get("url")
        if not url or not isinstance(url, str):
            return Tuple_Validation(is_valid=False, error="url must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.navigate(kwargs["url"])
        return ToolResult(success=res.get("success", True), data=res, error=res.get("error"))


class BrowserSearchTool(BaseTool):
    name = "browser_search"
    description = "Searches the web/internet via search engine or website search (Google, YouTube, Bing, DuckDuckGo) for online queries and web content. Use for internet searches like 'search YouTube for X' or 'search Google for X'."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "Search term/query string."
            },
            "engine": {
                "type": "STRING",
                "description": "Search engine or site name (google, youtube, bing, duckduckgo)."
            }
        },
        "required": ["query"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        q = kwargs.get("query")
        if not q or not isinstance(q, str):
            return Tuple_Validation(is_valid=False, error="query must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.search(kwargs["query"], engine=kwargs.get("engine", "google"))
        return ToolResult(success=res.get("success", True), data=res, error=res.get("error"))


class BrowserGetPageInfoTool(BaseTool):
    name = "browser_get_page_info"
    description = "Inspects active browser page and returns concise summary of links, buttons, and input fields."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.inspection.get_page_info()
        return ToolResult(success="error" not in res, data=res, error=res.get("error"))


class BrowserGetTextTool(BaseTool):
    name = "browser_get_text"
    description = "Extracts main visible text content from active browser page."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.inspection.get_visible_text()
        return ToolResult(success="error" not in res, data=res, error=res.get("error"))


class BrowserClickTool(BaseTool):
    name = "browser_click"
    description = "Clicks a web element identified by text, role, label, or selector."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "target": {
                "type": "STRING",
                "description": "Element text, label, or selector to click."
            }
        },
        "required": ["target"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        target = kwargs.get("target")
        if not target or not isinstance(target, str):
            return Tuple_Validation(is_valid=False, error="target must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.click(kwargs["target"])
        return ToolResult(success=res.get("success", False), data=res, error=res.get("error"))


class BrowserTypeTool(BaseTool):
    name = "browser_type"
    description = "Types text into an editable input field."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "selector_or_label": {
                "type": "STRING",
                "description": "Input field label, placeholder, or selector."
            },
            "text": {
                "type": "STRING",
                "description": "Text string to type."
            }
        },
        "required": ["selector_or_label", "text"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        lbl = kwargs.get("selector_or_label")
        txt = kwargs.get("text")
        if not lbl or not isinstance(lbl, str):
            return Tuple_Validation(is_valid=False, error="selector_or_label must be a string.")
        if txt is None or not isinstance(txt, str):
            return Tuple_Validation(is_valid=False, error="text must be a string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.type_text(kwargs["selector_or_label"], kwargs["text"])
        return ToolResult(success=res.get("success", False), data=res, error=res.get("error"))


class BrowserPressKeyTool(BaseTool):
    name = "browser_press_key"
    description = "Sends a keyboard key press (e.g. 'Enter', 'Tab', 'Escape') to the browser."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "key": {
                "type": "STRING",
                "description": "Keyboard key to press."
            }
        },
        "required": ["key"]
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.actions.press_key(kwargs.get("key", "Enter"))
        return ToolResult(success=res.get("success", True), data=res, error=res.get("error"))


class BrowserScrollTool(BaseTool):
    name = "browser_scroll"
    description = "Scrolls active browser page up or down."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "direction": {
                "type": "STRING",
                "description": "Scroll direction: 'down' or 'up'."
            },
            "amount": {
                "type": "INTEGER",
                "description": "Scroll pixel distance (default 500)."
            }
        },
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.actions.scroll(kwargs.get("direction", "down"), kwargs.get("amount", 500))
        return ToolResult(success=res.get("success", True), data=res, error=res.get("error"))


class BrowserBackTool(BaseTool):
    name = "browser_back"
    description = "Navigates back to the previous page in history."
    risk_level = RiskLevel.SAFE
    parameters = {"type": "OBJECT", "properties": {}, "required": []}

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.navigation.back()
        return ToolResult(success=res.get("success", True), data=res, error=res.get("error"))


class BrowserForwardTool(BaseTool):
    name = "browser_forward"
    description = "Navigates forward in page history."
    risk_level = RiskLevel.SAFE
    parameters = {"type": "OBJECT", "properties": {}, "required": []}

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.navigation.forward()
        return ToolResult(success=res.get("success", True), data=res, error=res.get("error"))


class BrowserNewTabTool(BaseTool):
    name = "browser_new_tab"
    description = "Opens a new browser tab with an optional URL."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "url": {
                "type": "STRING",
                "description": "Optional starting URL for new tab."
            }
        },
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        page = browser_manager.session.new_tab(kwargs.get("url"))
        return ToolResult(success=True, data={"title": page.title(), "url": page.url, "tabs": browser_manager.session.get_tabs_info()})


class BrowserSwitchTabTool(BaseTool):
    name = "browser_switch_tab"
    description = "Switches active browser tab by tab index (0-based) or title match."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "index_or_title": {
                "type": "STRING",
                "description": "Tab index integer string ('0', '1') or tab title keyword."
            }
        },
        "required": ["index_or_title"]
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        target = kwargs.get("index_or_title", 0)
        try:
            target = int(target)
        except ValueError:
            pass
        page = browser_manager.session.switch_tab(target)
        return ToolResult(success=True, data={"title": page.title(), "url": page.url, "tabs": browser_manager.session.get_tabs_info()})


class BrowserCloseTabTool(BaseTool):
    name = "browser_close_tab"
    description = "Closes active or target tab index."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "index": {
                "type": "INTEGER",
                "description": "Optional tab index to close."
            }
        },
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        browser_manager.session.close_tab(kwargs.get("index"))
        return ToolResult(success=True, data={"tabs": browser_manager.session.get_tabs_info()})


class BrowserScreenshotTool(BaseTool):
    name = "browser_screenshot"
    description = "Captures full screenshot of active browser page and saves to disk."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "output_path": {
                "type": "STRING",
                "description": "Optional output filepath for screenshot."
            }
        },
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.take_screenshot(kwargs.get("output_path"))
        return ToolResult(success=res.get("success", False), data=res, error=res.get("error"))


class BrowserDownloadTool(BaseTool):
    name = "browser_download"
    description = "Downloads a file from target URL or download link. Requires confirmation."
    risk_level = RiskLevel.CONFIRM
    parameters = {
        "type": "OBJECT",
        "properties": {
            "url_or_selector": {
                "type": "STRING",
                "description": "Download link URL or selector."
            }
        },
        "required": ["url_or_selector"]
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        res = browser_manager.downloads.download_file(kwargs["url_or_selector"])
        return ToolResult(success=res.get("success", False), data=res, error=res.get("error"))
