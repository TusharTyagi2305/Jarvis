import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("jarvis.audit")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

class AuditLogger:
    """
    Structured logger that records all user requests, tool calls, permission decisions, and execution outcomes.
    Ensures secrets and API keys are never written to log files.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            log_dir = Path("logs")
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.log_dir / "audit.jsonl"
        self._history: List[Dict[str, Any]] = []

    def _sanitize(self, data: Any) -> Any:
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                if any(secret_key in k.lower() for secret_key in ["key", "secret", "password", "token", "auth"]):
                    sanitized[k] = "***REDACTED***"
                else:
                    sanitized[k] = self._sanitize(v)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize(item) for item in data]
        return data

    def log_event(
        self,
        event_type: str,
        user_request: str,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        risk_level: Optional[str] = None,
        permission_result: Optional[str] = None,
        execution_result: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_request": user_request,
            "tool_name": tool_name,
            "tool_args": self._sanitize(tool_args) if tool_args else None,
            "risk_level": risk_level,
            "permission_result": permission_result,
            "execution_result": self._sanitize(execution_result) if execution_result else None,
            "duration_ms": duration_ms,
            "error": error
        }

        self._history.append(entry)
        
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log entry: {e}")

        logger.info(f"AUDIT [{event_type}] tool={tool_name} risk={risk_level} duration={duration_ms}ms error={error}")
        return entry

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-limit:]
