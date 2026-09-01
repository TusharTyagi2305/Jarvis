import enum
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

class RiskLevel(str, enum.Enum):
    SAFE = "SAFE"
    CONFIRM = "CONFIRM"
    DANGEROUS = "DANGEROUS"

@dataclass
class PermissionCheckResult:
    allowed: bool
    risk_level: RiskLevel
    requires_confirmation: bool
    reason: str
    confirmation_token: Optional[str] = None

class PermissionEngine:
    """
    Evaluates actions against security policies and manages confirmation requirements.
    """

    # Prohibited commands for safety
    PROHIBITED_COMMAND_PATTERNS = [
        "format ", "rmdir /s /q c:", "del /f /s /q c:",
        "drop database", "mkfs", "dd if=", ":(){ :|:& };:"
    ]

    def __init__(self, auto_approve_safe: bool = True):
        self.auto_approve_safe = auto_approve_safe
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}

    def evaluate_tool_execution(
        self,
        tool_name: str,
        base_risk_level: RiskLevel,
        parameters: Dict[str, Any]
    ) -> PermissionCheckResult:
        """
        Evaluates a tool invocation request based on tool base risk level and arguments.
        """
        effective_risk = base_risk_level

        # Contextual elevation of risk level based on parameters
        if tool_name == "terminal_command":
            cmd = str(parameters.get("command", "")).lower()
            # Check for prohibited dangerous destructive patterns
            for pattern in self.PROHIBITED_COMMAND_PATTERNS:
                if pattern in cmd:
                    return PermissionCheckResult(
                        allowed=False,
                        risk_level=RiskLevel.DANGEROUS,
                        requires_confirmation=False,
                        reason=f"Command contains prohibited dangerous operation pattern: '{pattern}'"
                    )
            # Elevate risk if command is destructive or modifies system state
            destructive_keywords = ["remove-item", "del", "rm", "git push", "pip install", "npm install", "shutdown", "restart"]
            if any(kw in cmd for kw in destructive_keywords):
                effective_risk = RiskLevel.CONFIRM

        elif tool_name == "delete_file":
            effective_risk = RiskLevel.CONFIRM

        elif tool_name in ["rename_move_file", "create_file"] and parameters.get("is_bulk", False):
            effective_risk = RiskLevel.CONFIRM

        if effective_risk == RiskLevel.SAFE:
            return PermissionCheckResult(
                allowed=True,
                risk_level=RiskLevel.SAFE,
                requires_confirmation=False,
                reason="SAFE action auto-approved."
            )
        
        # For CONFIRM or DANGEROUS, require explicit user confirmation
        token = f"confirm_{tool_name}_{hash(str(parameters))}"
        self._pending_confirmations[token] = {
            "tool_name": tool_name,
            "parameters": parameters,
            "risk_level": effective_risk
        }

        return PermissionCheckResult(
            allowed=False,
            risk_level=effective_risk,
            requires_confirmation=True,
            reason=f"Action '{tool_name}' classified as {effective_risk.value} requires user confirmation.",
            confirmation_token=token
        )

    def confirm_action(self, token: str) -> bool:
        """
        Confirms a pending action given its token.
        """
        if token in self._pending_confirmations:
            del self._pending_confirmations[token]
            return True
        return False
