import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class MemoryRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str = Field(description="Category e.g. preferences, projects, applications, workflows, instructions, facts.")
    content: str = Field(description="Content of the memory record.")
    source: str = Field(default="explicit_user_instruction", description="Source of memory record e.g. explicit_user_instruction, inferred.")
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    importance: float = Field(default=1.0, description="Importance score between 0.0 and 1.0.")
    confidence: float = Field(default=1.0, description="Confidence score between 0.0 and 1.0.")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowStep(BaseModel):
    tool_name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None

class WorkflowRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(description="Name/Alias of the workflow.")
    steps: List[WorkflowStep] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)

class WorkingMemoryState(BaseModel):
    current_task: Optional[str] = None
    recent_messages: List[Dict[str, str]] = Field(default_factory=list)
    recent_tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    active_window: Optional[str] = None
    browser_url: Optional[str] = None
