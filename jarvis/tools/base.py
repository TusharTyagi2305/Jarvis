from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from jarvis.security.permissions import RiskLevel

class ToolResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    recoverable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "recoverable": self.recoverable
        }

class BaseTool(ABC):
    """
    Abstract Base Class for all JARVIS tools.
    """

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema specification for function calling
    risk_level: RiskLevel = RiskLevel.SAFE

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Executes the tool with validated arguments and returns structured ToolResult.
        """
        pass

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        """
        Validates argument values before execution. Returns Tuple_Validation.
        """
        return Tuple_Validation(is_valid=True)

class Tuple_Validation(BaseModel):
    is_valid: bool
    error: Optional[str] = None
