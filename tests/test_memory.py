import pytest
from jarvis.memory.models import MemoryRecord
from jarvis.memory.policies import SensitiveDataFilter
from jarvis.memory.working import WorkingMemory
from jarvis.memory.providers.sqlite import SQLiteMemoryRepository
from jarvis.memory.manager import MemoryManager
from jarvis.tools.memory_tools import MemorySaveTool, MemorySearchTool, MemoryForgetTool
from jarvis.security.permissions import RiskLevel

def test_sensitive_data_filter():
    is_sens, reason = SensitiveDataFilter.is_sensitive("My password is SecretPass123!")
    assert is_sens is True
    assert "sensitive" in reason

    is_sens2, _ = SensitiveDataFilter.is_sensitive("My favorite browser is Chrome")
    assert is_sens2 is False

def test_working_memory():
    wm = WorkingMemory(max_history=5)
    wm.add_message("user", "Hello JARVIS")
    wm.add_message("jarvis", "Greetings sir")
    summary = wm.get_summary()
    assert len(summary["recent_messages"]) == 2

def test_sqlite_memory_repository(tmp_path):
    db_file = tmp_path / "test_jarvis.db"
    repo = SQLiteMemoryRepository(db_path_str=str(db_file))

    # Save
    rec = MemoryRecord(category="projects", content="LearnGen AI is main project")
    saved = repo.save_memory(rec)
    assert saved.id == rec.id

    # Search
    found = repo.search_memories(query="LearnGen")
    assert len(found) == 1
    assert found[0].content == "LearnGen AI is main project"

    # Delete
    deleted = repo.delete_memory(rec.id)
    assert deleted is True

def test_memory_manager_sensitive_blocking(tmp_path):
    repo = SQLiteMemoryRepository(db_path_str=str(tmp_path / "mem.db"))
    mgr = MemoryManager(repo=repo)

    success, msg = mgr.save_memory("credentials", "My api_key = sk-1234567890")
    assert success is False
    assert "blocked" in msg.lower()

def test_memory_manager_workflow_saving(tmp_path):
    repo = SQLiteMemoryRepository(db_path_str=str(tmp_path / "wf.db"))
    mgr = MemoryManager(repo=repo)

    steps = [
        {"tool_name": "open_application", "args": {"app_name": "notepad"}},
        {"tool_name": "get_system_info", "args": {}}
    ]
    wf = mgr.save_workflow("start dev", steps)
    assert wf.name == "start dev"

    retrieved = mgr.get_workflow("start dev")
    assert retrieved is not None
    assert len(retrieved.steps) == 2

def test_memory_tools_permissions():
    assert MemorySearchTool().risk_level == RiskLevel.SAFE
    assert MemorySaveTool().risk_level == RiskLevel.CONFIRM
    assert MemoryForgetTool().risk_level == RiskLevel.CONFIRM
