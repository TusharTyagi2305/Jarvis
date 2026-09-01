from typing import Dict, Any, Optional
from pydantic import BaseModel
import time

class WSEvent(BaseModel):
    type: str
    timestamp: float = time.time()

class StateEvent(WSEvent):
    type: str = "state"
    state: str  # IDLE, LISTENING, PROCESSING, PLANNING, EXECUTING, WAITING, COMPLETED, ERROR

class TaskStartedEvent(WSEvent):
    type: str = "task_started"
    task_id: str
    description: str

class ToolStartedEvent(WSEvent):
    type: str = "tool_started"
    tool: str
    args: Dict[str, Any]

class ToolCompletedEvent(WSEvent):
    type: str = "tool_completed"
    tool: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

class ConfirmationRequiredEvent(WSEvent):
    type: str = "confirmation_required"
    confirmation_id: str
    tool_name: str
    risk_level: str
    message: str
    parameters: Dict[str, Any]

class TaskCompletedEvent(WSEvent):
    type: str = "task_completed"
    task_id: str
    result: str
    success: bool

class ErrorEvent(WSEvent):
    type: str = "error"
    message: str

class TelemetryEvent(WSEvent):
    type: str = "telemetry"
    cpu: float
    ram: float
    disk: float
    battery: Optional[Dict[str, Any]] = None
    os_info: str

class VoiceStateEvent(WSEvent):
    type: str = "voice_state"
    voice_state: str  # IDLE, WAKE_LISTENING, WAKE_DETECTED, LISTENING, TRANSCRIBING, PROCESSING, SPEAKING, ERROR

class TranscriptEvent(WSEvent):
    type: str = "transcript"
    text: str
    confidence: Optional[float] = None
    is_final: bool = True

class SpeechStartedEvent(WSEvent):
    type: str = "speech_started"
    text: str

class SpeechCompletedEvent(WSEvent):
    type: str = "speech_completed"

class BrowserActionEvent(WSEvent):
    type: str = "browser_action"
    action: str
    target: str

class BrowserPageChangedEvent(WSEvent):
    type: str = "browser_page_changed"
    url: str
    title: str
    tabs: Optional[Any] = None

class ScreenAnalysisCompletedEvent(WSEvent):
    type: str = "screen_analysis_completed"
    description: str
    active_window: str
    elements_count: int
    image_path: Optional[str] = None

class ScreenElementFoundEvent(WSEvent):
    type: str = "screen_element_found"
    element_type: str
    text: str
    x: int
    y: int
    confidence: float

class ScreenActionEvent(WSEvent):
    type: str = "screen_action"
    action: str
    target: str

class MemorySavedEvent(WSEvent):
    type: str = "memory_saved"
    category: str
    content: str

class MemoryUpdatedEvent(WSEvent):
    type: str = "memory_updated"
    category: str
    content: str

class MemoryDeletedEvent(WSEvent):
    type: str = "memory_deleted"
    identifier: str

class MemoryBlockedEvent(WSEvent):
    type: str = "memory_blocked"
    reason: str

class TaskPlanCreatedEvent(WSEvent):
    type: str = "task_plan_created"
    plan_id: str
    goal: str
    steps_count: int

class TaskStepStartedEvent(WSEvent):
    type: str = "task_step_started"
    step_id: str
    description: str
    tool: Optional[str] = None

class TaskStepCompletedEvent(WSEvent):
    type: str = "task_step_completed"
    step_id: str
    result: Optional[str] = None

class TaskStepFailedEvent(WSEvent):
    type: str = "task_step_failed"
    step_id: str
    error: str

class TaskStepRetryingEvent(WSEvent):
    type: str = "task_step_retrying"
    step_id: str
    retry_count: int
    error: str

class TaskReplannedEvent(WSEvent):
    type: str = "task_replanned"
    plan_id: str
    reason: str

class TaskPausedEvent(WSEvent):
    type: str = "task_paused"
    plan_id: str

class TaskResumedEvent(WSEvent):
    type: str = "task_resumed"
    plan_id: str

class TaskCancelledEvent(WSEvent):
    type: str = "task_cancelled"
    plan_id: str
    reason: str

class TaskWaitingConfirmationEvent(WSEvent):
    type: str = "task_waiting_confirmation"
    step_id: str
    description: str
    tool: str

class TaskGoalVerifiedEvent(WSEvent):
    type: str = "task_goal_verified"
    plan_id: str
    goal: str
    verified: bool
