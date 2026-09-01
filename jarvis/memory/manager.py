import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from jarvis.config import settings
from jarvis.memory.models import MemoryRecord, WorkflowRecord
from jarvis.memory.policies import SensitiveDataFilter, ConsentPolicy
from jarvis.memory.working import WorkingMemory
from jarvis.memory.providers.sqlite import SQLiteMemoryRepository
from jarvis.memory.providers.vector import VectorMemoryProvider
from jarvis.memory.retrieval import MemoryRetriever

logger = logging.getLogger("jarvis.memory.manager")

class MemoryManager:
    """
    Central Memory Manager unifying Short-Term Working Memory, Structured SQLite Memory, Vector Memory, and Privacy Policies.
    """

    def __init__(
        self,
        repo: Optional[SQLiteMemoryRepository] = None,
        working_memory: Optional[WorkingMemory] = None
    ):
        self.repo = repo or SQLiteMemoryRepository(db_path_str=settings.memory_db_path)
        self.working = working_memory or WorkingMemory()
        self.vector = VectorMemoryProvider()
        self.retriever = MemoryRetriever(self.repo, self.vector)

    def _emit_event(self, event_obj: Any):
        try:
            from jarvis.api.websocket import ws_manager
            ws_manager.broadcast_event_sync(event_obj)
        except Exception:
            pass

    def save_memory(self, category: str, content: str, source: str = "explicit_user_instruction") -> Tuple[bool, str]:
        if not settings.memory_enabled:
            return False, "Memory system is currently disabled."

        # 1. Privacy & Sensitive Data Filter
        is_sens, reason = SensitiveDataFilter.is_sensitive(content)
        if is_sens:
            self._emit_event_blocked(reason)
            return False, f"Memory blocked: {reason}"

        # 2. Consent Policy
        if not ConsentPolicy.can_persist(source):
            return False, "Automatic memory persistence is disabled by policy."

        record = MemoryRecord(
            category=category.strip().lower(),
            content=content.strip(),
            source=source
        )
        self.repo.save_memory(record)
        self._emit_event_saved(record)
        return True, f"Memory saved under category '{record.category}'."

    def search_memories(self, query: str = "", category: Optional[str] = None, limit: int = 5) -> List[MemoryRecord]:
        return self.retriever.retrieve(query=query, limit=limit)

    def list_memories(self, category: Optional[str] = None, limit: int = 20) -> List[MemoryRecord]:
        return self.repo.search_memories(category=category, limit=limit)

    def delete_memory(self, identifier: str) -> bool:
        success = self.repo.delete_memory(identifier)
        if success:
            self._emit_event_deleted(identifier)
        return success

    def forget_everything(self) -> bool:
        count = self.repo.delete_all()
        self.working.clear()
        logger.info(f"Memory reset complete. Deleted {count} records.")
        return True

    def save_workflow(self, name: str, steps: List[Dict[str, Any]]) -> WorkflowRecord:
        record = self.repo.save_workflow(name, steps)
        return record

    def get_workflow(self, name: str) -> Optional[WorkflowRecord]:
        return self.repo.get_workflow(name)

    def export_memories(self, file_path_str: Optional[str] = None) -> Dict[str, Any]:
        memories = self.repo.search_memories(limit=500)
        workflows = self.repo.list_workflows()

        export_data = {
            "version": "1.0",
            "exported_at": Path().stat().st_mtime if Path().exists() else 0,
            "memories": [m.model_dump() for m in memories],
            "workflows": [w.model_dump() for w in workflows]
        }

        if file_path_str:
            p = Path(file_path_str).resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(export_data, indent=2), encoding="utf-8")

        return export_data

    def _emit_event_saved(self, record: MemoryRecord):
        try:
            from jarvis.api.events import MemorySavedEvent
            self._emit_event(MemorySavedEvent(category=record.category, content=record.content))
        except Exception:
            pass

    def _emit_event_deleted(self, identifier: str):
        try:
            from jarvis.api.events import MemoryDeletedEvent
            self._emit_event(MemoryDeletedEvent(identifier=identifier))
        except Exception:
            pass

    def _emit_event_blocked(self, reason: str):
        try:
            from jarvis.api.events import MemoryBlockedEvent
            self._emit_event(MemoryBlockedEvent(reason=reason))
        except Exception:
            pass

class Tuple_Save_Result:
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message

    def __iter__(self):
        return iter((self.success, self.message))

# Singleton MemoryManager instance
memory_manager = MemoryManager()
