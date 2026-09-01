import pytest
from jarvis.brain.mock import MockLLMProvider
from jarvis.tools import create_default_registry
from jarvis.security.permissions import PermissionEngine
from jarvis.security.audit import AuditLogger
from jarvis.orchestrator.agent_loop import JarvisOrchestrator

def test_orchestrator_system_info_intent(tmp_path):
    audit_logger = AuditLogger(log_dir=tmp_path / "logs")
    orchestrator = JarvisOrchestrator(
        llm_provider=MockLLMProvider(),
        tool_registry=create_default_registry(),
        permission_engine=PermissionEngine(),
        audit_logger=audit_logger
    )

    response = orchestrator.run("Jarvis, check my system info and battery level")
    assert response.success is True
    assert len(response.plan.steps) > 0
    assert response.plan.steps[0].tool_name == "get_system_info"
    assert response.plan.steps[0].status == "COMPLETED"

def test_orchestrator_permission_required(tmp_path):
    audit_logger = AuditLogger(log_dir=tmp_path / "logs")
    permission_engine = PermissionEngine()
    orchestrator = JarvisOrchestrator(
        llm_provider=MockLLMProvider(),
        tool_registry=create_default_registry(),
        permission_engine=permission_engine,
        audit_logger=audit_logger
    )

    # Request that gets mapped to terminal command with destructive keyword or delete
    response = orchestrator.run("delete file test_output.txt")
    assert response.pending_confirmation is not None
    assert response.pending_confirmation["tool_name"] == "delete_file" or "confirmation" in response.final_response.lower()

    # Now simulate user confirming
    token = response.pending_confirmation["token"]
    permission_engine.confirm_action(token)

    res_after = orchestrator.run("delete file test_output.txt", confirmed_tokens=[token])
    # Now it proceeds past confirmation check
    assert res_after.pending_confirmation is None

def test_tool_routing_regressions(tmp_path, monkeypatch):
    audit_logger = AuditLogger(log_dir=tmp_path / "logs")
    orchestrator = JarvisOrchestrator(
        llm_provider=MockLLMProvider(),
        tool_registry=create_default_registry(),
        permission_engine=PermissionEngine(),
        audit_logger=audit_logger
    )

    # Mock actual browser & vision execution so unit tests don't interact with GUI/network
    monkeypatch.setattr("jarvis.browser.manager.browser_manager.navigate", lambda url: {"success": True, "url": url})
    monkeypatch.setattr("jarvis.browser.manager.browser_manager.search", lambda q, engine="google": {"success": True, "query": q})
    monkeypatch.setattr("jarvis.vision.analyzer.screen_analyzer.find_element", lambda target, confidence_threshold=0.85: None)

    # 1. "open YouTube" -> browser_navigate
    res1 = orchestrator.run("open YouTube")
    assert res1.plan.steps[0].tool_name == "browser_navigate"

    # 2. "search YouTube for hasmob002" -> browser_search
    res2 = orchestrator.run("search YouTube for hasmob002")
    assert res2.plan.steps[0].tool_name == "browser_search"

    # 3. "open YouTube and search hasmob002" -> browser_navigate + browser_search
    res3 = orchestrator.run("open YouTube and search hasmob002")
    tool_names_3 = [s.tool_name for s in res3.plan.steps]
    assert "browser_navigate" in tool_names_3
    assert "browser_search" in tool_names_3
    assert "search_files" not in tool_names_3

    # 4. "find all Python files" -> search_files
    res4 = orchestrator.run("find all Python files")
    assert res4.plan.steps[0].tool_name == "search_files"

    # 5. "what do you remember about my project?" -> memory_search
    res5 = orchestrator.run("what do you remember about my project?")
    assert res5.plan.steps[0].tool_name == "memory_search"

    # 6. "find the Run button" -> screen_find_element
    res6 = orchestrator.run("find the Run button")
    assert res6.plan.steps[0].tool_name == "screen_find_element"

    # 7. "open Notepad" -> open_application
    res7 = orchestrator.run("open Notepad")
    assert res7.plan.steps[0].tool_name == "open_application"

