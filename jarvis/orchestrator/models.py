import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from jarvis.security.permissions import RiskLevel

class StepStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"

class TaskStep(BaseModel):
    id: str = Field(default_factory=lambda: f"step_{str(uuid.uuid4())[:8]}")
    description: str
    depends_on: List[str] = Field(default_factory=list, description="IDs of steps that must complete first.")
    tool: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = Field(default=RiskLevel.SAFE)
    status: StepStatus = Field(default=StepStatus.PENDING)
    retry_count: int = Field(default=0)
    result: Optional[Any] = None
    error: Optional[str] = None

class TaskPlan(BaseModel):
    id: str = Field(default_factory=lambda: f"plan_{str(uuid.uuid4())[:8]}")
    goal: str
    steps: List[TaskStep] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    status: str = Field(default="PLANNING", description="PLANNING, EXECUTING, VERIFYING, WAITING, PAUSED, COMPLETED, FAILED, CANCELLED")
    max_iterations: int = Field(default=50)

class TaskObservation(BaseModel):
    success: bool
    summary: str
    raw_error: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    state_changes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0)

# Legacy compatibility models for phase 1 agent loop
class ExecutionStep(BaseModel):
    step_number: int
    thought: str
    action_name: str
    action_args: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None

class ExecutionPlan(BaseModel):
    user_request: str
    steps: List[ExecutionStep] = Field(default_factory=list)

class AgentResponse(BaseModel):
    user_request: str
    plan: ExecutionPlan
    final_response: str
    success: bool
    execution_time_seconds: float
