import time
import queue
import logging
import uuid
from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from jarvis.config import settings

logger = logging.getLogger("jarvis.command_bus")

class CommandMessage(BaseModel):
    command_id: str = Field(default_factory=lambda: f"CMD_{uuid.uuid4().hex[:8]}")
    source: str = Field(default="text")  # "voice", "text", "hotkey"
    user_request: str
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CommandBus:
    """
    Unified thread-safe command queue for Voice, Text, and Hotkey commands.
    Prevents parallel execution race conditions and provides structured pipeline logging.
    """

    def __init__(self):
        self._queue = queue.Queue()
        self.is_processing = False

    def submit(self, user_request: str, source: str = "text", metadata: Optional[Dict[str, Any]] = None) -> CommandMessage:
        msg = CommandMessage(source=source, user_request=user_request, metadata=metadata or {})
        if settings.jarvis_debug_pipeline:
            logger.info(f"[{msg.command_id}] Submitted via source='{source}': '{user_request}'")
        self._queue.put(msg)
        return msg

    def get_next(self, block: bool = True, timeout: Optional[float] = None) -> Optional[CommandMessage]:
        try:
            return self._queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def task_done(self):
        self._queue.task_done()

# Singleton CommandBus
command_bus = CommandBus()
