import logging
import urllib.parse
from typing import Dict, Any
from jarvis.browser.session import BrowserSession

logger = logging.getLogger("jarvis.browser.navigation")

class NavigationManager:
    """
    Handles browser page navigation, search engine searching, and history traversal.
    """

    def __init__(self, session: BrowserSession):
        self.session = session

    def navigate(self, url: str) -> Dict[str, Any]:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        page = self.session.get_active_page()
        try:
            response = page.goto(url, timeout=15000, wait_until="commit")
            status = response.status if response else 200
            title = page.title()
            current_url = page.url
            return {
                "success": True,
                "url": current_url,
                "title": title,
                "status": status
            }
        except Exception as e:
            logger.error(f"Failed to navigate to '{url}': {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    def search(self, query: str, engine: str = "google") -> Dict[str, Any]:
        encoded_query = urllib.parse.quote_plus(query)
        if engine.lower() == "duckduckgo":
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        elif engine.lower() == "bing":
            search_url = f"https://www.bing.com/search?q={encoded_query}"
        elif engine.lower() == "youtube":
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        else:
            search_url = f"https://www.google.com/search?q={encoded_query}"

        return self.navigate(search_url)

    def back(self) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            page.go_back(timeout=10000)
            return {"success": True, "url": page.url, "title": page.title()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def forward(self) -> Dict[str, Any]:
        page = self.session.get_active_page()
        try:
            page.go_forward(timeout=10000)
            return {"success": True, "url": page.url, "title": page.title()}
        except Exception as e:
            return {"success": False, "error": str(e)}
