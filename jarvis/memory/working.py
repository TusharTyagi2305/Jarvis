import logging
from typing import Dict, Any, List, Optional
from jarvis.memory.models import WorkingMemoryState

logger = logging.getLogger("jarvis.memory.working")

class WorkingMemory:
    """
    Manages short-term task and session working memory.
    """

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.state = WorkingMemoryState()

    def update_task(self, task_description: str):
        self.state.current_task = task_description

    def add_message(self, sender: str, text: str):
        self.state.recent_messages.append({"sender": sender, "text": text})
        if len(self.state.recent_messages) > self.max_history:
            self.state.recent_messages = self.state.recent_messages[-self.max_history:]

    def add_tool_result(self, tool_name: str, result: Any):
        self.state.recent_tool_results.append({"tool": tool_name, "result": result})
        if len(self.state.recent_tool_results) > 10:
            self.state.recent_tool_results = self.state.recent_tool_results[-10:]

    def update_context(self, active_window: Optional[str] = None, browser_url: Optional[str] = None):
        if active_window:
            self.state.active_window = active_window
        if browser_url:
            self.state.browser_url = browser_url

    def get_summary(self) -> Dict[str, Any]:
        return self.state.model_dump()

    def clear(self):
        self.state = WorkingMemoryState()
