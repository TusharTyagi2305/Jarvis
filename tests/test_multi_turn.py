import sys
import io
import logging
import pytest

from jarvis.config import settings
from jarvis.brain.mock import MockLLMProvider
from jarvis.tools import create_default_registry, ToolResult
from jarvis.security.permissions import PermissionEngine
from jarvis.security.audit import AuditLogger
from jarvis.orchestrator.agent_loop import JarvisOrchestrator

def test_multi_turn_bharu_flow():
    settings.gemini_api_key = ""
    audit_logger = AuditLogger()
    tool_registry = create_default_registry()

    # Intercept browser tools to prevent Playwright greenlet thread switching in unit tests
    def mock_browser_search(query: str, engine: str = "youtube"):
        return ToolResult(
            success=True,
            data={"query": query, "url": f"https://www.youtube.com/results?search_query={query}"},
            output_summary=f"Found results for '{query}'"
        )
    
    def mock_browser_nav(url: str):
        return ToolResult(
            success=True,
            data={"url": url, "title": "YouTube"},
            output_summary=f"Navigated to {url}"
        )

    def mock_browser_click(target: str):
        return ToolResult(
            success=True,
            data={"target": target},
            output_summary=f"Clicked {target}"
        )

    def mock_desktop_type(text: str):
        return ToolResult(
            success=True,
            data={"text": text},
            output_summary=f"Typed '{text}'"
        )

    def mock_create_file(file_path: str, content: str = ""):
        return ToolResult(
            success=True,
            data={"file_path": file_path, "content": content},
            output_summary=f"Created file {file_path}"
        )

    def mock_open_app(app_name: str):
        return ToolResult(
            success=True,
            data={"app_name": app_name},
            output_summary=f"Opened {app_name}"
        )

    orig_execute = tool_registry.execute_tool
    def mock_execute_tool(name: str, kwargs: dict):
        if name == "browser_search":
            return mock_browser_search(**kwargs)
        elif name == "browser_navigate":
            return mock_browser_nav(**kwargs)
        elif name == "browser_click":
            return mock_browser_click(**kwargs)
        elif name == "create_file":
            return mock_create_file(**kwargs)
        elif name == "open_application":
            return mock_open_app(**kwargs)
        return orig_execute(name, kwargs)

    tool_registry.execute_tool = mock_execute_tool

    permission_engine = PermissionEngine()
    permission_engine.evaluate = lambda tool_name, args, **kwargs: __import__('jarvis.security.permissions', fromlist=['RiskDecision']).RiskDecision(allow=True, requires_confirmation=False, risk_level=__import__('jarvis.security.permissions', fromlist=['RiskLevel']).RiskLevel.LOW, reason="Test auto-allow")
    llm = MockLLMProvider()

    orchestrator = JarvisOrchestrator(
        llm_provider=llm,
        tool_registry=tool_registry,
        permission_engine=permission_engine,
        audit_logger=audit_logger
    )

    test_cases = [
        ("Jarvis YouTube kholo.", ["YouTube", "khola", "khol"]),
        ("Hasmob002 search karo.", ["hasmob002", "results"]),
        ("Channel kholo.", ["Channel", "khol"]),
        ("Iska sabse popular video chalao.", ["Popular video", "chala"]),
        ("Jarvis Notepad kholo.", ["Notepad", "Application", "खोल", "khol"]),
        ("Isme likho: mera interview kal hai.", ["Likh", "written", "file", "bana", "create"]),
        ("Jarvis battery kitni hai?", ["Battery", "System", "info"])
    ]

    for idx, (query, expected_keywords) in enumerate(test_cases, 1):
        resp = orchestrator.run(user_request=query)
        final_text = resp.final_response

        # Verify no raw tool/dict leaks
        assert "{" not in final_text and "}" not in final_text, f"FAILED TEST {idx}: Raw dict in output!"
        assert "Task action complete" not in final_text, f"FAILED TEST {idx}: Internal debug text in output!"
        assert "status_code" not in final_text and "200" not in final_text, f"FAILED TEST {idx}: Raw HTTP status in output!"

        # Verify proper response text
        has_match = any(kw.lower() in final_text.lower() for kw in expected_keywords)
        assert has_match, f"Expected one of {expected_keywords} in '{final_text}'"
