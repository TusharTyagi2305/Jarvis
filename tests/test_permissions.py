import pytest
from jarvis.security.permissions import PermissionEngine, RiskLevel

def test_permission_safe_tool():
    engine = PermissionEngine()
    result = engine.evaluate_tool_execution(
        tool_name="get_system_info",
        base_risk_level=RiskLevel.SAFE,
        parameters={}
    )
    assert result.allowed is True
    assert result.requires_confirmation is False
    assert result.risk_level == RiskLevel.SAFE

def test_permission_confirm_destructive_command():
    engine = PermissionEngine()
    result = engine.evaluate_tool_execution(
        tool_name="terminal_command",
        base_risk_level=RiskLevel.SAFE,
        parameters={"command": "rm -rf /some/path"}
    )
    assert result.allowed is False
    assert result.requires_confirmation is True
    assert result.risk_level == RiskLevel.CONFIRM
    assert result.confirmation_token is not None

def test_permission_prohibited_dangerous_command():
    engine = PermissionEngine()
    result = engine.evaluate_tool_execution(
        tool_name="terminal_command",
        base_risk_level=RiskLevel.SAFE,
        parameters={"command": "format c:"}
    )
    assert result.allowed is False
    assert result.requires_confirmation is False
    assert result.risk_level == RiskLevel.DANGEROUS
    assert "prohibited" in result.reason.lower()

def test_permission_confirmation_flow():
    engine = PermissionEngine()
    result = engine.evaluate_tool_execution(
        tool_name="delete_file",
        base_risk_level=RiskLevel.SAFE,
        parameters={"file_path": "important.txt"}
    )
    token = result.confirmation_token
    assert token is not None

    # Confirming valid token
    assert engine.confirm_action(token) is True
    # Second attempt should return False as token is consumed
    assert engine.confirm_action(token) is False
