import pytest
from jarvis.orchestrator.models import TaskPlan, TaskStep, StepStatus
from jarvis.orchestrator.task_engine import TaskPlanEngine
from jarvis.security.permissions import PermissionEngine, RiskLevel
from jarvis.security.terminal_classifier import TerminalSafetyClassifier
from jarvis.tools import create_default_registry

def test_terminal_safety_classifier():
    assert TerminalSafetyClassifier.classify("git status") == RiskLevel.SAFE
    assert TerminalSafetyClassifier.classify("python --version") == RiskLevel.SAFE
    assert TerminalSafetyClassifier.classify("npm install axios") == RiskLevel.SAFE
    assert TerminalSafetyClassifier.classify("rm -rf /") == RiskLevel.CONFIRM
    assert TerminalSafetyClassifier.classify("del /f /s C:\\*") == RiskLevel.CONFIRM

def test_plan_dependency_validation():
    registry = create_default_registry()
    engine = TaskPlanEngine(tool_registry=registry, permission_engine=PermissionEngine())

    # Valid plan
    step1 = TaskStep(id="s1", description="Get info", tool="get_system_info")
    step2 = TaskStep(id="s2", description="Take screenshot", tool="take_screenshot", depends_on=["s1"])
    plan = TaskPlan(goal="Check system", steps=[step1, step2])

    valid, err = engine.validate_plan(plan)
    assert valid is True

    # Missing dependency
    step_bad = TaskStep(id="s3", description="Bad step", tool="get_system_info", depends_on=["non_existent"])
    plan_bad = TaskPlan(goal="Bad plan", steps=[step_bad])
    valid_bad, err_bad = engine.validate_plan(plan_bad)
    assert valid_bad is False
    assert "non-existent" in err_bad

    # Circular dependency
    step_a = TaskStep(id="sa", description="A", tool="get_system_info", depends_on=["sb"])
    step_b = TaskStep(id="sb", description="B", tool="get_system_info", depends_on=["sa"])
    plan_circ = TaskPlan(goal="Circular plan", steps=[step_a, step_b])
    valid_circ, err_circ = engine.validate_plan(plan_circ)
    assert valid_circ is False
    assert "Circular dependency" in err_circ

def test_task_plan_engine_execution():
    registry = create_default_registry()
    engine = TaskPlanEngine(tool_registry=registry, permission_engine=PermissionEngine())

    s1 = TaskStep(id="s1", description="Step 1", tool="get_system_info")
    s2 = TaskStep(id="s2", description="Step 2", tool="take_screenshot", depends_on=["s1"])
    plan = TaskPlan(goal="Execute 2 steps", steps=[s1, s2])

    res = engine.execute_plan(plan)
    assert res["success"] is True
    assert res["status"] == "COMPLETED"
    assert s1.status == StepStatus.COMPLETED
    assert s2.status == StepStatus.COMPLETED

def test_task_engine_pause_resume_cancel():
    registry = create_default_registry()
    engine = TaskPlanEngine(tool_registry=registry, permission_engine=PermissionEngine())

    s1 = TaskStep(id="s1", description="Step 1", tool="get_system_info")
    plan = TaskPlan(goal="Pause test", steps=[s1])

    engine.pause()
    assert engine.is_paused is True

    engine.resume()
    assert engine.is_paused is False

    engine.cancel()
    assert engine.is_cancelled is True
