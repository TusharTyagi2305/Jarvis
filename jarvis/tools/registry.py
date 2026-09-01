import logging
import asyncio
import concurrent.futures
from typing import Dict, List, Any, Optional, Type
from jarvis.tools.base import BaseTool, ToolResult

logger = logging.getLogger("jarvis.tools.registry")

_GLOBAL_TOOL_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="jarvis_tool_worker")

def execute_on_tool_thread(fn, *args, timeout=60, **kwargs):
    future = _GLOBAL_TOOL_EXECUTOR.submit(fn, *args, **kwargs)
    return future.result(timeout=timeout)

class ToolRegistry:
    """
    Central registry for managing, validating, and executing JARVIS tools.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._executor = _GLOBAL_TOOL_EXECUTOR

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            logger.warning(f"Overwriting tool registration for '{tool.name}'")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}' (Risk: {tool.risk_level})")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_gemini_tool_declarations(self) -> List[Dict[str, Any]]:
        """
        Converts registered tools into function declarations format required by Gemini.
        """
        declarations = []
        for tool in self._tools.values():
            declarations.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            })
        return declarations

    def execute_tool(self, name: str, kwargs: Dict[str, Any]) -> ToolResult:
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{name}' is not registered in the Tool Registry.",
                recoverable=True
            )
        try:
            val = tool.validate(**kwargs)
            if not val.is_valid:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Validation failed for tool '{name}': {val.error}",
                    recoverable=True
                )
            
            return execute_on_tool_thread(tool.execute, **kwargs)
        except Exception as e:
            logger.exception(f"Unhandled exception during tool '{name}' execution")
            return ToolResult(
                success=False,
                data=None,
                error=f"Exception during tool execution: {str(e)}",
                recoverable=True
            )
