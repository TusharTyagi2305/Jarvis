import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("jarvis.browser.session")

class BrowserSession:
    """
    Manages Playwright browser lifecycle, tabs/pages, active page tracking, and tab operations.
    """

    def __init__(self, headless: Optional[bool] = None):
        if headless is None:
            from jarvis.config import settings
            self.headless = settings.browser_headless
        else:
            self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._pages: List[Any] = []
        self._active_page_index: int = -1

    def ensure_browser(self):
        """
        Ensures Playwright browser instance is initialized and running.
        """
        if self._browser and self._browser.is_connected():
            return

        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            self._context = self._browser.new_context(
                accept_downloads=True,
                viewport={"width": 1280, "height": 720}
            )
            # Create initial tab
            page = self._context.new_page()
            self._pages = [page]
            self._active_page_index = 0
            logger.info(f"Playwright Chromium browser session initialized (headless={self.headless}).")
        except Exception as e:
            logger.error(f"Failed to launch Playwright browser: {e}")
            raise e

    def get_active_page(self):
        self.ensure_browser()
        if not self._pages or self._active_page_index < 0 or self._active_page_index >= len(self._pages):
            page = self._context.new_page()
            self._pages.append(page)
            self._active_page_index = len(self._pages) - 1
        return self._pages[self._active_page_index]

    def new_tab(self, url: Optional[str] = None):
        self.ensure_browser()
        page = self._context.new_page()
        self._pages.append(page)
        self._active_page_index = len(self._pages) - 1
        if url:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
        return page

    def switch_tab(self, index_or_title: Any):
        self.ensure_browser()
        if isinstance(index_or_title, int):
            if 0 <= index_or_title < len(self._pages):
                self._active_page_index = index_or_title
                return self._pages[self._active_page_index]
        elif isinstance(index_or_title, str):
            for idx, p in enumerate(self._pages):
                try:
                    if index_or_title.lower() in p.title().lower() or index_or_title.lower() in p.url.lower():
                        self._active_page_index = idx
                        return p
                except Exception:
                    continue
        return self.get_active_page()

    def close_tab(self, index: Optional[int] = None):
        if not self._pages:
            return
        target_idx = index if index is not None else self._active_page_index
        if 0 <= target_idx < len(self._pages):
            page = self._pages.pop(target_idx)
            try:
                page.close()
            except Exception:
                pass
            if not self._pages:
                self._active_page_index = -1
            else:
                self._active_page_index = max(0, min(target_idx, len(self._pages) - 1))

    def get_tabs_info(self) -> List[Dict[str, Any]]:
        tabs = []
        for idx, p in enumerate(self._pages):
            try:
                tabs.append({
                    "index": idx,
                    "title": p.title(),
                    "url": p.url,
                    "is_active": (idx == self._active_page_index)
                })
            except Exception:
                tabs.append({"index": idx, "title": "Unknown", "url": "", "is_active": (idx == self._active_page_index)})
        return tabs

    def close_all(self):
        def _close():
            try:
                if self._context:
                    self._context.close()
                if self._browser:
                    self._browser.close()
                if self._playwright:
                    self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error closing browser session: {e}")
            finally:
                self._pages = []
                self._active_page_index = -1
                self._browser = None
                self._context = None
                self._playwright = None

        try:
            from jarvis.tools.registry import execute_on_tool_thread
            return execute_on_tool_thread(_close, timeout=10)
        except Exception:
            _close()
