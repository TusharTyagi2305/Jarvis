import subprocess
import platform
from typing import Dict, Any
from jarvis.tools.base import BaseTool, ToolResult, Tuple_Validation
from jarvis.security.permissions import RiskLevel

class TerminalCommandTool(BaseTool):
    name = "terminal_command"
    description = "Executes a terminal/PowerShell command securely in a controlled subprocess with output capturing."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "command": {
                "type": "STRING",
                "description": "Terminal command to execute."
            },
            "cwd": {
                "type": "STRING",
                "description": "Optional working directory in which to execute the command."
            },
            "timeout_seconds": {
                "type": "INTEGER",
                "description": "Timeout limit in seconds (default 30)."
            }
        },
        "required": ["command"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        cmd = kwargs.get("command")
        if not cmd or not isinstance(cmd, str):
            return Tuple_Validation(is_valid=False, error="command must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        cmd = kwargs["command"].strip()
        cwd = kwargs.get("cwd")
        timeout = kwargs.get("timeout_seconds", 30)

        # Shell selection based on OS
        if platform.system() == "Windows":
            shell_cmd = ["powershell", "-NoProfile", "-Command", cmd]
        else:
            shell_cmd = ["/bin/bash", "-c", cmd]

        try:
            result = subprocess.run(
                shell_cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            exit_code = result.returncode

            success = (exit_code == 0)
            return ToolResult(
                success=success,
                data={
                    "command": cmd,
                    "exit_code": exit_code,
                    "stdout": stdout[:10000],  # Cap output size
                    "stderr": stderr[:5000]
                },
                error=stderr if not success else None,
                recoverable=True
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error=f"Terminal command timed out after {timeout} seconds.",
                recoverable=True
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to execute terminal command: {str(e)}",
                recoverable=True
            )
