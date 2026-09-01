from typing import Dict, Any
from jarvis.tools.base import BaseTool, ToolResult, Tuple_Validation
from jarvis.security.permissions import RiskLevel
from jarvis.memory.manager import memory_manager

class MemorySaveTool(BaseTool):
    name = "memory_save"
    description = "Saves a persistent memory record under a category (preferences, projects, workflows, instructions)."
    risk_level = RiskLevel.CONFIRM
    parameters = {
        "type": "OBJECT",
        "properties": {
            "category": {
                "type": "STRING",
                "description": "Category e.g. preferences, projects, workflows, instructions."
            },
            "content": {
                "type": "STRING",
                "description": "Information/fact content to save."
            }
        },
        "required": ["category", "content"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        c = kwargs.get("category")
        txt = kwargs.get("content")
        if not c or not isinstance(c, str):
            return Tuple_Validation(is_valid=False, error="category must be a non-empty string.")
        if not txt or not isinstance(txt, str):
            return Tuple_Validation(is_valid=False, error="content must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        success, msg = memory_manager.save_memory(kwargs["category"], kwargs["content"])
        return ToolResult(success=success, data={"message": msg}, error=None if success else msg)


class MemorySearchTool(BaseTool):
    name = "memory_search"
    description = "Searches long-term structured and semantic memory database for stored user facts, project info, and remembered context."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "Search query or keyword."
            },
            "category": {
                "type": "STRING",
                "description": "Optional category filter."
            }
        },
        "required": ["query"]
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        records = memory_manager.search_memories(kwargs.get("query", ""), kwargs.get("category"))
        return ToolResult(success=True, data=[r.model_dump() for r in records])


class MemoryGetTool(BaseTool):
    name = "memory_get"
    description = "Retrieves stored workflow or memory preference by name."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "name": {
                "type": "STRING",
                "description": "Workflow name or preference key."
            }
        },
        "required": ["name"]
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        name = kwargs.get("name", "")
        wf = memory_manager.get_workflow(name)
        if wf:
            return ToolResult(success=True, data=wf.model_dump())

        records = memory_manager.search_memories(query=name, limit=1)
        if records:
            return ToolResult(success=True, data=records[0].model_dump())
        return ToolResult(success=False, error=f"No memory record or workflow found for '{name}'.")


class MemoryUpdateTool(BaseTool):
    name = "memory_update"
    description = "Updates an existing memory record."
    risk_level = RiskLevel.CONFIRM
    parameters = {
        "type": "OBJECT",
        "properties": {
            "category": {
                "type": "STRING",
                "description": "Memory category."
            },
            "content": {
                "type": "STRING",
                "description": "Updated content."
            }
        },
        "required": ["category", "content"]
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        success, msg = memory_manager.save_memory(kwargs["category"], kwargs["content"])
        return ToolResult(success=success, data={"message": msg})


class MemoryDeleteTool(BaseTool):
    name = "memory_delete"
    description = "Deletes a specific memory record or workflow by identifier or keyword."
    risk_level = RiskLevel.CONFIRM
    parameters = {
        "type": "OBJECT",
        "properties": {
            "identifier": {
                "type": "STRING",
                "description": "Memory ID, keyword, or category to delete."
            }
        },
        "required": ["identifier"]
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        success = memory_manager.delete_memory(kwargs.get("identifier", ""))
        return ToolResult(success=success, data={"deleted": success})


class MemoryListTool(BaseTool):
    name = "memory_list"
    description = "Lists all stored memory records and categories."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "category": {
                "type": "STRING",
                "description": "Optional category filter."
            }
        },
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        records = memory_manager.list_memories(kwargs.get("category"))
        return ToolResult(success=True, data=[r.model_dump() for r in records])


class MemoryForgetTool(BaseTool):
    name = "memory_forget"
    description = "Deletes ALL saved long-term memories and workflows (Requires User Confirmation)."
    risk_level = RiskLevel.CONFIRM
    parameters = {"type": "OBJECT", "properties": {}, "required": []}

    def execute(self, **kwargs: Any) -> ToolResult:
        success = memory_manager.forget_everything()
        return ToolResult(success=success, data={"message": "All memories deleted successfully."})
