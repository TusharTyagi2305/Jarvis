import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import psutil

from jarvis.browser.session import BrowserSession
from jarvis.browser.navigation import NavigationManager
from jarvis.browser.inspection import InspectionManager
from jarvis.browser.actions import ActionManager
from jarvis.browser.downloads import DownloadManager

logger = logging.getLogger("jarvis.browser.manager")

class BrowserManager:
    """
    Unified Browser Manager orchestrating Playwright sessions, navigation, inspection, actions, downloads, screenshots, and WebSocket broadcasting.
    """

    def __init__(self, headless: Optional[bool] = None):
        self.session = BrowserSession(headless=headless)
        self.navigation = NavigationManager(self.session)
        self.inspection = InspectionManager(self.session)
        self.actions = ActionManager(self.session)
        self.downloads = DownloadManager(self.session)

    def _emit_event(self, event_obj: Any):
        try:
            from jarvis.api.websocket import ws_manager
            ws_manager.broadcast_event_sync(event_obj)
        except Exception:
            pass

    def open_browser(self, initial_url: str = "https://www.google.com") -> Dict[str, Any]:
        res = self.navigation.navigate(initial_url)
        self._emit_event_page_changed()
        return res

    def navigate(self, url: str) -> Dict[str, Any]:
        self._emit_event_action("navigate", url)
        res = self.navigation.navigate(url)
        self._emit_event_page_changed()
        return res

    def search(self, query: str, engine: str = "google") -> Dict[str, Any]:
        self._emit_event_action("search", f"{query} via {engine}")
        res = self.navigation.search(query, engine)
        self._emit_event_page_changed()
        return res

    def click(self, target: str) -> Dict[str, Any]:
        self._emit_event_action("click", target)
        res = self.actions.click(target)
        self._emit_event_page_changed()
        return res

    def type_text(self, selector_or_label: str, text: str) -> Dict[str, Any]:
        self._emit_event_action("type", f"text into '{selector_or_label}'")
        res = self.actions.type_text(selector_or_label, text)
        self._emit_event_page_changed()
        return res

    def take_screenshot(self, output_path_str: Optional[str] = None) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            if not output_path_str:
                shots_dir = Path("screenshots")
                shots_dir.mkdir(exist_ok=True)
                output_path = shots_dir / f"browser_screenshot_{int(psutil.time.time())}.png"
            else:
                output_path = Path(output_path_str).resolve()
                output_path.parent.mkdir(parents=True, exist_ok=True)

            page.screenshot(path=str(output_path), full_page=False)
            return {
                "success": True,
                "path": str(output_path),
                "url": page.url,
                "title": page.title()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _emit_event_action(self, action_name: str, target: str):
        try:
            from jarvis.api.events import BrowserActionEvent
            self._emit_event(BrowserActionEvent(action=action_name, target=target))
        except Exception:
            pass

    def _emit_event_page_changed(self):
        try:
            from jarvis.api.events import BrowserPageChangedEvent
            page = self.session.get_active_page()
            tabs = self.session.get_tabs_info()
            self._emit_event(BrowserPageChangedEvent(
                url=page.url,
                title=page.title(),
                tabs=tabs
            ))
        except Exception:
            pass

# Singleton BrowserManager instance
browser_manager = BrowserManager()
