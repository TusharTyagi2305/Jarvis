from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ToolCallRequest(BaseModel):
    id: Optional[str] = None
    tool_name: str
    args: Dict[str, Any]

class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: List[ToolCallRequest] = []
    finish_reason: Optional[str] = None

class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM models supporting tool calling.
    Allows hot-swapping between Gemini, Mock provider, or future LLM providers.
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None
    ) -> LLMResponse:
        """
        Generates a completion response given current conversation history and tool declarations.
        """
        pass
