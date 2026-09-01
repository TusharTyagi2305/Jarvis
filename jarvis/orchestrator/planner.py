import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Step(BaseModel):
    step_id: int
    description: str
    tool_name: Optional[str] = None
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, FAILED, CONFIRMATION_REQUIRED
    result: Optional[Any] = None
    error: Optional[str] = None

class ExecutionPlan(BaseModel):
    user_request: str
    steps: List[Step] = []
    created_at: float = Field(default_factory=time.time)
    completed: bool = False
