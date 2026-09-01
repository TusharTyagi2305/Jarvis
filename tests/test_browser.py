import pytest
from jarvis.tools.browser_tools import (
    BrowserOpenTool,
    BrowserNavigateTool,
    BrowserSearchTool,
    BrowserGetPageInfoTool,
    BrowserGetTextTool,
    BrowserClickTool,
    BrowserTypeTool,
    BrowserScreenshotTool,
    BrowserDownloadTool,
    BrowserNewTabTool,
    BrowserSwitchTabTool,
    BrowserCloseTabTool
)
from jarvis.security.permissions import RiskLevel

def test_browser_tool_risk_levels():
    nav_tool = BrowserNavigateTool()
    assert nav_tool.risk_level == RiskLevel.SAFE

    dl_tool = BrowserDownloadTool()
    assert dl_tool.risk_level == RiskLevel.CONFIRM

def test_browser_tool_validation():
    nav_tool = BrowserNavigateTool()
    v1 = nav_tool.validate(url="https://google.com")
    assert v1.is_valid is True

    v2 = nav_tool.validate(url="")
    assert v2.is_valid is False

    click_tool = BrowserClickTool()
    v3 = click_tool.validate(target="Search")
    assert v3.is_valid is True

def test_browser_execution_mocked(monkeypatch):
    class MockBrowserManager:
        def open_browser(self, url):
            return {"success": True, "url": url, "title": "Google"}
        def navigate(self, url):
            return {"success": True, "url": url, "title": "GitHub"}
        def search(self, query, engine="google"):
            return {"success": True, "query": query, "url": "https://google.com"}

    mock_mgr = MockBrowserManager()
    monkeypatch.setattr("jarvis.tools.browser_tools.browser_manager", mock_mgr)

    open_tool = BrowserOpenTool()
    res1 = open_tool.execute(url="https://google.com")
    assert res1.success is True
    assert res1.data["url"] == "https://google.com"

    nav_tool = BrowserNavigateTool()
    res2 = nav_tool.execute(url="https://github.com")
    assert res2.success is True
    assert res2.data["title"] == "GitHub"

    search_tool = BrowserSearchTool()
    res3 = search_tool.execute(query="Python FastAPI")
    assert res3.success is True

def test_browser_headless_config():
    from jarvis.config import settings
    from jarvis.browser.session import BrowserSession
    assert settings.browser_headless is False
    session = BrowserSession()
    assert session.headless is False
