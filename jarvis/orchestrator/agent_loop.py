import time
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from jarvis.config import settings
from jarvis.brain.base import BaseLLMProvider, ToolCallRequest
from jarvis.tools.registry import ToolRegistry
from jarvis.tools.base import ToolResult
from jarvis.security.permissions import PermissionEngine, RiskLevel
from jarvis.security.audit import AuditLogger
from jarvis.orchestrator.planner import ExecutionPlan, Step

logger = logging.getLogger("jarvis.orchestrator")

SYSTEM_PROMPT = """You are JARVIS, a personal desktop AI assistant.
Your communication style:
- DEFAULT LANGUAGE: Hindi/Hinglish-first. Understand Hindi, English, and Hinglish natively.
- Match user language: If user speaks Hindi -> respond in Hindi. English -> English. Hinglish -> Hinglish.
- Keep responses extremely CONCISE: Exactly 1 short natural sentence (e.g. "YouTube खोल दिया.", "hasmob002 ke results mil gaye.", "Notepad khol diya hai.", "Battery 70% hai.").
- DO NOT speak or output raw dictionaries, JSON, tool names, HTTP status codes, stack traces, URLs, or internal implementation details.
- DO NOT force translation of proper nouns (YouTube, Chrome, VS Code, GitHub, Notepad, LearnGen AI, Hasmob002).
- Execute actions autonomously via registered tools without explaining internal steps.

CRITICAL TOOL SELECTION RULES:
1. Web / Online Search / Browsing: Use `browser_navigate` to open websites (e.g. YouTube, Google) and `browser_search` to search online query terms. DO NOT use `search_files` for web requests.
2. Local File Search: Use `search_files` ONLY to find local files or scripts on disk (e.g. *.py, project files).
3. Memory Search: Use `memory_search` for queries asking what JARVIS remembers about user preferences, facts, or projects.
4. Screen Vision: Use `screen_find_element` or `screen_analyze` to locate UI buttons/elements on the desktop screen.
"""

class AgentResponse(BaseModel):
    user_request: str
    final_response: str
    iterations: int
    pending_confirmation: Optional[Dict[str, Any]] = None
    plan: ExecutionPlan
    success: bool
    audit_history: List[Dict[str, Any]] = []

class JarvisOrchestrator:
    """
    Main orchestrator implementing the 14-step Agent Execution Loop.
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        tool_registry: ToolRegistry,
        permission_engine: PermissionEngine,
        audit_logger: AuditLogger,
        max_iterations: int = 10
    ):
        self.llm = llm_provider
        self.tools = tool_registry
        self.permissions = permission_engine
        self.audit = audit_logger
        self.max_iterations = max_iterations

        from jarvis.orchestrator.task_engine import TaskPlanEngine
        self.engine = TaskPlanEngine(tool_registry=tool_registry, permission_engine=permission_engine)

    def validate_and_sanitize_tool_call(self, user_request: str, tool_name: str, tool_args: Dict[str, Any]):
        req_lower = user_request.lower()
        from jarvis.context import active_context

        # 1. Notepad / App Launch Guard
        if "notepad" in req_lower:
            if "close" in req_lower or "band" in req_lower:
                return "close_application", {"process_name": "notepad.exe"}
            return "open_application", {"app_name": "notepad"}

        # 2. Contextual Follow-Up Guard (Channel / Video / Search)
        if any(kw in req_lower for kw in ["channel", "most watched", "popular", "play", "video"]):
            if "channel" in req_lower:
                active_context.last_target_channel = active_context.last_search_query or "hasmob002"
                return "browser_click", {"target": "channel"}
            elif any(kw in req_lower for kw in ["popular", "most watched", "video", "play"]):
                return "browser_click", {"target": "most watched video"}

        # 3. Web / Browser Intent Guard
        if any(term in req_lower for term in ["youtube", "google", "bing", "website", "web", "internet", "browser", "url", "search"]):
            if tool_name in ["search_files", "browser_navigate"] and "search" in req_lower:
                if "youtube" in req_lower or "hasmob002" in req_lower or active_context.active_browser_domain == "www.youtube.com":
                    q = req_lower.replace("youtube", "").replace("search", "").replace("karo", "").replace("dhundho", "").replace("dhoondho", "").replace("par", "").replace("pe", "").strip() or "hasmob002"
                    active_context.last_search_query = q
                    return "browser_search", {"query": q, "engine": "youtube"}

        # 4. File Search Intent Guard
        if any(term in req_lower for term in ["python files", "my project files", "find files", "search files in", "find *.py"]):
            if tool_name in ["browser_search", "browser_navigate", "memory_search"]:
                pattern = "*.py" if "python" in req_lower or ".py" in req_lower else "*.*"
                return "search_files", {"directory": ".", "pattern": pattern}

        # 5. Memory Search Intent Guard
        if any(term in req_lower for term in ["what do you remember", "what is my project", "remember about", "stored memory"]):
            if tool_name in ["search_files", "browser_search"]:
                return "memory_search", {"query": user_request}

        return tool_name, tool_args

    def run(
        self,
        user_request: str,
        confirmed_tokens: Optional[List[str]] = None,
        event_listener: Optional[Any] = None
    ) -> AgentResponse:
        """
        Executes the agent loop for a user request.
        """
        from jarvis.api.websocket import ws_manager
        from jarvis.api.events import (
            StateEvent, TaskStartedEvent, ToolStartedEvent, ToolCompletedEvent,
            ConfirmationRequiredEvent, TaskCompletedEvent, ErrorEvent
        )

        def emit(evt):
            try:
                ws_manager.broadcast_event_sync(evt)
            except Exception as ex:
                logger.debug(f"WS broadcast warning: {ex}")
            if event_listener:
                try:
                    event_listener(evt)
                except Exception:
                    pass

        task_id = f"task_{int(time.time() * 1000)}"
        emit(StateEvent(state="PROCESSING"))
        emit(TaskStartedEvent(task_id=task_id, description=user_request))

        start_time = time.time()
        confirmed_tokens = confirmed_tokens or []

        # 1. Update Active Working Context & Memory
        from jarvis.context import active_context
        from jarvis.brain.response_formatter import ResponseFormatter

        resolved_request = active_context.resolve_pronouns(user_request)
        active_context.last_user_command = user_request

        if "search" in resolved_request.lower():
            parts = resolved_request.lower().split("search")
            active_context.last_search_query = parts[-1].replace("for", "").strip()

        from jarvis.memory.manager import memory_manager
        memory_manager.working.add_message("user", resolved_request)
        memory_manager.working.update_task(resolved_request)

        relevant_mems = memory_manager.search_memories(resolved_request, limit=settings.memory_max_results)
        mem_context = memory_manager.retriever.format_context_for_prompt(relevant_mems)

        augmented_request = resolved_request
        if mem_context:
            augmented_request = f"{mem_context}\n\nUser Request: {resolved_request}"

        # Build messages including recent conversation history turns from active_context
        messages: List[Dict[str, Any]] = []
        for turn in active_context.conversation_turns:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": augmented_request})
        
        plan = ExecutionPlan(user_request=user_request)
        iteration = 0
        final_answer = ""
        pending_confirmation_info = None

        tool_schemas = self.tools.get_gemini_tool_declarations()

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Agent Loop Iteration {iteration}/{self.max_iterations}")

            emit(StateEvent(state="PLANNING"))

            # 2 & 3 & 4. Understand intent, determine tool requirements, get LLM reasoning
            llm_res = self.llm.generate(
                messages=messages,
                tools=tool_schemas,
                system_instruction=SYSTEM_PROMPT
            )

            # If LLM produces direct text answer without tool calls
            if llm_res.content and not llm_res.tool_calls:
                final_answer = llm_res.content
                plan.completed = True
                break

            # Process requested tool calls
            if llm_res.tool_calls:
                all_tools_succeeded = True
                
                for tool_call in llm_res.tool_calls:
                    tool_name, tool_args = self.validate_and_sanitize_tool_call(user_request, tool_call.tool_name, tool_call.args)
                    
                    step_num = len(plan.steps) + 1
                    step = Step(step_id=step_num, description=f"Execute tool '{tool_name}'", tool_name=tool_name)
                    plan.steps.append(step)

                    # 5. Select tool & 6. Check permission level
                    target_tool = self.tools.get_tool(tool_name)
                    if target_tool:
                        val_res = target_tool.validate(**tool_args)
                        if not val_res.is_valid:
                            logger.warning(f"Tool argument validation failed for '{tool_name}': {val_res.error}")
                            step.status = "FAILED"
                            step.error = f"Invalid tool arguments: {val_res.error}"
                            all_tools_succeeded = False
                            continue

                    base_risk = target_tool.risk_level if target_tool else RiskLevel.SAFE
                    
                    perm_check = self.permissions.evaluate_tool_execution(
                        tool_name=tool_name,
                        base_risk_level=base_risk,
                        parameters=tool_args
                    )

                    # 7. Ask for confirmation if required (unless token was pre-approved)
                    if perm_check.requires_confirmation:
                        token = perm_check.confirmation_token
                        if token not in confirmed_tokens:
                            step.status = "CONFIRMATION_REQUIRED"
                            pending_confirmation_info = {
                                "token": token,
                                "tool_name": tool_name,
                                "tool_args": tool_args,
                                "risk_level": perm_check.risk_level.value,
                                "reason": perm_check.reason
                            }
                            self.audit.log_event(
                                event_type="TOOL_CONFIRMATION_REQUESTED",
                                user_request=user_request,
                                tool_name=tool_name,
                                tool_args=tool_args,
                                risk_level=perm_check.risk_level.value,
                                permission_result="PENDING_CONFIRMATION"
                            )
                            final_answer = f"I need your explicit confirmation before proceeding with '{tool_name}'. Action risk level: {perm_check.risk_level.value}."
                            emit(StateEvent(state="WAITING"))
                            emit(ConfirmationRequiredEvent(
                                confirmation_id=token,
                                tool_name=tool_name,
                                risk_level=perm_check.risk_level.value,
                                message=f"Confirm action '{tool_name}' ({perm_check.risk_level.value})",
                                parameters=tool_args
                            ))
                            return AgentResponse(
                                user_request=user_request,
                                final_response=final_answer,
                                iterations=iteration,
                                pending_confirmation=pending_confirmation_info,
                                plan=plan,
                                success=False,
                                audit_history=self.audit.get_history()
                            )

                    # 8. Execute Tool
                    emit(StateEvent(state="EXECUTING"))
                    emit(ToolStartedEvent(tool=tool_name, args=tool_args))
                    t_start = time.time()
                    tool_result: ToolResult = self.tools.execute_tool(tool_name, tool_args)
                    duration_ms = round((time.time() - t_start) * 1000, 2)

                    emit(ToolCompletedEvent(
                        tool=tool_name,
                        success=tool_result.success,
                        result=tool_result.data,
                        error=tool_result.error
                    ))

                    # 9. Capture result & 10. Observe result
                    step.result = tool_result.data
                    step.error = tool_result.error

                    self.audit.log_event(
                        event_type="TOOL_EXECUTION",
                        user_request=user_request,
                        tool_name=tool_name,
                        tool_args=tool_args,
                        risk_level=base_risk.value,
                        permission_result="APPROVED",
                        execution_result=tool_result.to_dict(),
                        duration_ms=duration_ms,
                        error=tool_result.error
                    )

                    if tool_result.success:
                        step.status = "COMPLETED"
                        active_context.last_successful_tool = tool_name
                        if tool_name.startswith("browser_"):
                            try:
                                from jarvis.browser.manager import browser_manager
                                page = browser_manager.session.get_active_page()
                                active_context.update_browser_state(page.url, page.title())
                            except Exception:
                                pass

                        # Feed observation back to conversation history
                        messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": str(tool_result.data)
                        })
                    else:
                        step.status = "FAILED"
                        all_tools_succeeded = False
                        # 11 & 12. Re-plan if error is recoverable
                        messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": f"Error executing tool '{tool_name}': {tool_result.error}. Re-plan or fix arguments."
                        })

                if all_tools_succeeded:
                    # Let the LLM construct the final user response based on tool observations
                    continue
            else:
                final_answer = "No further actions required."
                plan.completed = True
                break

        # 13. Max iterations safeguard
        if iteration >= self.max_iterations and not final_answer:
            final_answer = "Main is task ko finish nahi kar paaya."

        tool_results_summary = [s.model_dump() for s in plan.steps] if plan.steps else []
        resp_text = ResponseFormatter.format_final_response(
            raw_response=final_answer or "Task completed.",
            user_request=user_request,
            tool_results=tool_results_summary
        )
        is_success = all([s.status == "COMPLETED" for s in plan.steps]) if plan.steps else True

        # Append turns to active_context for multi-turn conversational history
        active_context.add_turn("user", user_request)
        active_context.add_turn("assistant", resp_text)

        emit(TaskCompletedEvent(
            task_id=task_id,
            result=resp_text,
            success=is_success
        ))
        emit(StateEvent(state="COMPLETED" if is_success else "ERROR"))

        # 14. Return concise final response
        return AgentResponse(
            user_request=user_request,
            final_response=resp_text,
            iterations=iteration,
            pending_confirmation=None,
            plan=plan,
            success=is_success,
            audit_history=self.audit.get_history()
        )
