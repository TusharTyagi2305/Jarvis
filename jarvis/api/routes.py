import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jarvis.config import settings
from jarvis.brain.gemini import GeminiLLMProvider
from jarvis.brain.mock import MockLLMProvider
from jarvis.tools import create_default_registry
from jarvis.security.permissions import PermissionEngine
from jarvis.security.audit import AuditLogger
from jarvis.orchestrator.agent_loop import JarvisOrchestrator, AgentResponse

router = APIRouter(prefix="/api", tags=["jarvis"])

# Singleton instances for API service
tool_registry = create_default_registry()
permission_engine = PermissionEngine()
audit_logger = AuditLogger()

if settings.gemini_api_key:
    llm_provider = GeminiLLMProvider(api_key=settings.gemini_api_key, model_name=settings.llm_model)
else:
    llm_provider = MockLLMProvider()

orchestrator = JarvisOrchestrator(
    llm_provider=llm_provider,
    tool_registry=tool_registry,
    permission_engine=permission_engine,
    audit_logger=audit_logger,
    max_iterations=settings.max_agent_iterations
)

class ChatRequest(BaseModel):
    query: str
    confirmed_tokens: Optional[List[str]] = None

class ConfirmRequest(BaseModel):
    token: str
    original_query: str

@router.post("/chat", response_model=AgentResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    response = orchestrator.run(
        user_request=request.query,
        confirmed_tokens=request.confirmed_tokens
    )
    return response

@router.post("/confirm", response_model=AgentResponse)
async def confirm_endpoint(request: ConfirmRequest):
    confirmed = permission_engine.confirm_action(request.token)
    if not confirmed:
        raise HTTPException(status_code=404, detail="Invalid or expired confirmation token.")
    
    # Re-run user query with token in pre-approved confirmed_tokens list
    response = orchestrator.run(
        user_request=request.original_query,
        confirmed_tokens=[request.token]
    )
    return response

class CommandRequest(BaseModel):
    command: str

@router.post("/command")
async def command_endpoint(request: CommandRequest):
    if not request.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty.")
    
    # Execute orchestrator with WebSocket event streaming
    response = orchestrator.run(
        user_request=request.command
    )

    # Speak response and emit TTS WebSocket event
    from jarvis.brain.response_formatter import ResponseFormatter
    spoken_text = ResponseFormatter.format_final_response(response.final_response, user_request=request.command)
    if response.pending_confirmation:
        spoken_text = f"Action {response.pending_confirmation['tool_name']} requires confirmation."
    
    voice_manager.speak_response(spoken_text)

    return {
        "status": "completed" if response.success else ("confirmation_required" if response.pending_confirmation else "failed"),
        "task_id": f"task_{int(time.time()*1000)}",
        "response": response
    }

from jarvis.voice.manager import VoiceManager
voice_manager = VoiceManager(orchestrator=orchestrator)

class SpeakRequest(BaseModel):
    text: str

class VoiceListenRequest(BaseModel):
    text_override: Optional[str] = None

@router.post("/voice/listen")
async def voice_listen_endpoint(request: Optional[VoiceListenRequest] = None):
    text_override = request.text_override if request else None
    response = voice_manager.process_voice_command(text_override=text_override)
    return {
        "status": "completed" if response.success else ("confirmation_required" if response.pending_confirmation else "failed"),
        "response": response
    }

@router.post("/voice/speak")
async def voice_speak_endpoint(request: SpeakRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    success = voice_manager.speak_response(request.text)
    return {"status": "success" if success else "failed", "text": request.text}

@router.get("/history")
async def get_history(limit: int = 50):
    return audit_logger.get_history(limit=limit)

@router.get("/system")
async def get_system_metrics():
    tool = tool_registry.get_tool("get_system_info")
    if not tool:
        raise HTTPException(status_code=500, detail="System info tool missing.")
    res = tool.execute()
    return res.to_dict()

@router.post("/task/pause")
def pause_task():
    orchestrator.engine.pause()
    return {"status": "PAUSED", "message": "Task paused."}

@router.post("/task/resume")
def resume_task():
    orchestrator.engine.resume()
    return {"status": "EXECUTING", "message": "Task resumed."}

@router.post("/task/cancel")
def cancel_task():
    orchestrator.engine.cancel()
    return {"status": "CANCELLED", "message": "Task cancelled."}

@router.get("/task/status")
def get_task_status():
    plan = orchestrator.engine.current_plan
    if not plan:
        return {"status": "IDLE", "plan": None}
    return {"status": plan.status, "plan": plan.model_dump()}

@router.get("/health")
def health_check():
    from jarvis.diagnostics import StartupDiagnostics
    diag = StartupDiagnostics.check_environment()
    return {
        "status": "healthy",
        "version": settings.jarvis_version,
        "subsystems": diag
    }
