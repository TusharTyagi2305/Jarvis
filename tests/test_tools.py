import os
import pytest
from pathlib import Path
from jarvis.tools import create_default_registry, ToolResult

def test_tool_registry_registration():
    registry = create_default_registry()
    tools = registry.list_tools()
    tool_names = [t.name for t in tools]
    
    expected_tools = [
        "get_system_info", "take_screenshot", "open_application", "close_application",
        "read_file", "create_file", "create_folder", "search_files", "rename_move_file",
        "terminal_command"
    ]
    for t_name in expected_tools:
        assert t_name in tool_names

def test_system_info_tool():
    registry = create_default_registry()
    res = registry.execute_tool("get_system_info", {})
    assert res.success is True
    assert "cpu_usage_percent" in res.data
    assert "os" in res.data

def test_file_operations_lifecycle(tmp_path):
    registry = create_default_registry()
    
    test_folder = tmp_path / "jarvis_test_dir"
    test_file = test_folder / "hello.txt"
    renamed_file = test_folder / "hello_renamed.txt"

    # 1. Create Folder
    res = registry.execute_tool("create_folder", {"folder_path": str(test_folder)})
    assert res.success is True
    assert test_folder.exists()

    # 2. Create File
    res = registry.execute_tool("create_file", {"file_path": str(test_file), "content": "Hello JARVIS System"})
    assert res.success is True
    assert test_file.exists()

    # 3. Read File
    res = registry.execute_tool("read_file", {"file_path": str(test_file)})
    assert res.success is True
    assert res.data["content"] == "Hello JARVIS System"

    # 4. Search Files
    res = registry.execute_tool("search_files", {"directory": str(test_folder), "pattern": "*.txt"})
    assert res.success is True
    assert res.data["total_found"] == 1

    # 5. Rename/Move File
    res = registry.execute_tool("rename_move_file", {"source_path": str(test_file), "destination_path": str(renamed_file)})
    assert res.success is True
    assert not test_file.exists()
    assert renamed_file.exists()

def test_terminal_command_tool():
    registry = create_default_registry()
    res = registry.execute_tool("terminal_command", {"command": "echo 'JARVIS Test'"})
    assert res.success is True
    assert "JARVIS Test" in res.data["stdout"]
