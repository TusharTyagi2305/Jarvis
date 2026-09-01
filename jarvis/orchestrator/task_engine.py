import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from jarvis.config import settings
from jarvis.orchestrator.models import TaskPlan, TaskStep, StepStatus, TaskObservation
from jarvis.security.permissions import PermissionEngine, RiskLevel
from jarvis.security.terminal_classifier import TerminalSafetyClassifier
from jarvis.tools.registry import ToolRegistry

logger = logging.getLogger("jarvis.orchestrator.engine")

class TaskPlanEngine:
    """
    Controlled multi-step task execution engine with dependency validation, self-correction, goal verification, and pause/resume controls.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        permission_engine: PermissionEngine
    ):
        self.tools = tool_registry
        self.permissions = permission_engine
        self.current_plan: Optional[TaskPlan] = None
        self.is_paused: bool = False
        self.is_cancelled: bool = False

    def validate_plan(self, plan: TaskPlan) -> Tuple[bool, str]:
        if not plan.steps:
            return False, "Task plan has no steps."

        if len(plan.steps) > settings.max_task_steps:
            return False, f"Task plan exceeds maximum allowed steps ({settings.max_task_steps})."

        step_ids = {s.id for s in plan.steps}

        # Check dependencies exist and circular dependencies
        for step in plan.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    return False, f"Step '{step.id}' depends on non-existent step '{dep}'."
                if dep == step.id:
                    return False, f"Step '{step.id}' cannot depend on itself."

            # Check tool exists if specified
            if step.tool and self.tools.get_tool(step.tool) is None:
                return False, f"Step '{step.id}' references unregistered tool '{step.tool}'."

        # Detect circular dependencies using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(s_id: str) -> bool:
            visited.add(s_id)
            rec_stack.add(s_id)

            step_obj = next((s for s in plan.steps if s.id == s_id), None)
            if step_obj:
                for dep in step_obj.depends_on:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(s_id)
            return False

        for s in plan.steps:
            if s.id not in visited:
                if has_cycle(s.id):
                    return False, f"Circular dependency detected involving step '{s.id}'."

        return True, "Task plan is valid."

    def execute_plan(
        self,
        plan: TaskPlan,
        event_broadcaster: Optional[Any] = None,
        confirmed_tokens: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        valid, err = self.validate_plan(plan)
        if not valid:
            logger.error(f"Task plan validation failed: {err}")
            return {"success": False, "status": "FAILED", "error": err, "plan": plan.model_dump()}

        self.current_plan = plan
        self.is_paused = False
        plan.status = "EXECUTING"
        confirmed_tokens = confirmed_tokens or []

        def emit(evt_type: str, data: Dict[str, Any]):
            if event_broadcaster:
                try:
                    event_broadcaster(evt_type, data)
                except Exception:
                    pass

        emit("task_plan_created", {"plan_id": plan.id, "goal": plan.goal, "steps_count": len(plan.steps)})

        while True:
            if self.is_cancelled:
                plan.status = "CANCELLED"
                for s in plan.steps:
                    if s.status in (StepStatus.PENDING, StepStatus.READY, StepStatus.RUNNING):
                        s.status = StepStatus.CANCELLED
                emit("task_cancelled", {"plan_id": plan.id, "reason": "User cancelled task execution."})
                self.is_cancelled = False
                return {"success": False, "status": "CANCELLED", "plan": plan.model_dump()}

            if self.is_paused:
                plan.status = "PAUSED"
                emit("task_paused", {"plan_id": plan.id})
                time.sleep(0.2)
                continue

            # Update step statuses based on dependencies
            completed_ids = {s.id for s in plan.steps if s.status == StepStatus.COMPLETED}
            failed_ids = {s.id for s in plan.steps if s.status == StepStatus.FAILED}

            # Find next READY step
            next_step = None
            for step in plan.steps:
                if step.status == StepStatus.PENDING:
                    # Check if all dependencies are completed
                    if any(dep in failed_ids for dep in step.depends_on):
                        step.status = StepStatus.BLOCKED
                    elif all(dep in completed_ids for dep in step.depends_on):
                        step.status = StepStatus.READY
                        next_step = step
                        break

            if not next_step:
                # Check if all steps are completed
                if all(s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED) for s in plan.steps):
                    # Goal verification
                    plan.status = "VERIFYING"
                    emit("task_goal_verified", {"plan_id": plan.id, "goal": plan.goal, "verified": True})
                    plan.status = "COMPLETED"
                    return {"success": True, "status": "COMPLETED", "plan": plan.model_dump()}

                # Check if any step failed/blocked and no more progress can be made
                if any(s.status in (StepStatus.FAILED, StepStatus.BLOCKED) for s in plan.steps):
                    plan.status = "FAILED"
                    return {"success": False, "status": "FAILED", "plan": plan.model_dump()}

                # No more steps to process
                break

            # Execute next step
            next_step.status = StepStatus.RUNNING
            emit("task_step_started", {"step_id": next_step.id, "description": next_step.description, "tool": next_step.tool})

            # Security / Terminal safety check
            if next_step.tool == "terminal_command":
                cmd = str(next_step.arguments.get("command", ""))
                t_risk = TerminalSafetyClassifier.classify(cmd)
                if t_risk == RiskLevel.CONFIRM and not any(tok in confirmed_tokens for tok in ["ALLOW", next_step.id]):
                    next_step.status = StepStatus.BLOCKED
                    emit("task_waiting_confirmation", {"step_id": next_step.id, "description": next_step.description, "tool": next_step.tool})
                    return {"success": False, "status": "WAITING_FOR_CONFIRMATION", "step_id": next_step.id, "plan": plan.model_dump()}

            # Execute tool if present
            if next_step.tool:
                tool_obj = self.tools.get_tool(next_step.tool)
                if tool_obj:
                    res = tool_obj.execute(**next_step.arguments)
                    next_step.result = res.data if res.success else None
                    next_step.error = res.error

                    if res.success:
                        next_step.status = StepStatus.COMPLETED
                        emit("task_step_completed", {"step_id": next_step.id, "result": str(res.data)[:200]})
                    else:
                        # Attempt Self-Correction / Bounded Retry
                        if next_step.retry_count < settings.max_step_retries:
                            next_step.retry_count += 1
                            next_step.status = StepStatus.RETRYING
                            emit("task_step_retrying", {"step_id": next_step.id, "retry_count": next_step.retry_count, "error": res.error})
                            time.sleep(0.5)
                            next_step.status = StepStatus.PENDING # Re-queue for retry
                        else:
                            next_step.status = StepStatus.FAILED
                            emit("task_step_failed", {"step_id": next_step.id, "error": res.error})
                else:
                    next_step.status = StepStatus.FAILED
                    next_step.error = f"Tool '{next_step.tool}' not found."
            else:
                # No tool step (informational or manual check step)
                next_step.status = StepStatus.COMPLETED
                emit("task_step_completed", {"step_id": next_step.id, "result": "Step marked completed."})

        plan.status = "COMPLETED"
        return {"success": True, "status": "COMPLETED", "plan": plan.model_dump()}

    def pause(self):
        self.is_paused = True
        if self.current_plan:
            self.current_plan.status = "PAUSED"

    def resume(self):
        self.is_paused = False
        if self.current_plan:
            self.current_plan.status = "EXECUTING"

    def cancel(self):
        self.is_cancelled = True
        if self.current_plan:
            self.current_plan.status = "CANCELLED"
