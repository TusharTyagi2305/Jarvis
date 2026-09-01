import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from jarvis.memory.models import MemoryRecord, WorkflowRecord, WorkflowStep

logger = logging.getLogger("jarvis.memory.sqlite")

class SQLiteMemoryRepository:
    """
    SQLite repository for persistent structured memory records and workflows.
    Data path: data/memory/jarvis_memory.db
    """

    def __init__(self, db_path_str: str = "data/memory/jarvis_memory.db"):
        self.db_path = Path(db_path_str).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                importance REAL NOT NULL,
                confidence REAL NOT NULL,
                metadata TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                steps TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            """)
            conn.commit()
        logger.info(f"SQLite memory database initialized at '{self.db_path}'.")

    def save_memory(self, record: MemoryRecord) -> MemoryRecord:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO memories (id, category, content, source, created_at, updated_at, importance, confidence, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                record.id,
                record.category.lower(),
                record.content,
                record.source,
                record.created_at,
                record.updated_at,
                record.importance,
                record.confidence,
                json.dumps(record.metadata)
            ))
            conn.commit()
        return record

    def search_memories(self, query: str = "", category: Optional[str] = None, limit: int = 10) -> List[MemoryRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM memories WHERE 1=1"
            params: List[Any] = []

            if category:
                sql += " AND category = ?"
                params.append(category.lower())

            if query:
                sql += " AND (content LIKE ? OR metadata LIKE ?)"
                q_pattern = f"%{query}%"
                params.extend([q_pattern, q_pattern])

            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            records = []
            for row in rows:
                records.append(MemoryRecord(
                    id=row["id"],
                    category=row["category"],
                    content=row["content"],
                    source=row["source"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    importance=row["importance"],
                    confidence=row["confidence"],
                    metadata=json.loads(row["metadata"] or "{}")
                ))
            return records

    def delete_memory(self, memory_id_or_keyword: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ? OR content LIKE ? OR category = ?;",
                           (memory_id_or_keyword, f"%{memory_id_or_keyword}%", memory_id_or_keyword.lower()))
            conn.commit()
            return cursor.rowcount > 0

    def delete_all(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories;")
            cursor.execute("DELETE FROM workflows;")
            conn.commit()
            return cursor.rowcount

    def save_workflow(self, name: str, steps: List[Dict[str, Any]]) -> WorkflowRecord:
        steps_objs = [WorkflowStep(**s) if isinstance(s, dict) else s for s in steps]
        record = WorkflowRecord(name=name.lower(), steps=steps_objs)
        steps_json = json.dumps([s.model_dump() for s in steps_objs])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO workflows (id, name, steps, created_at)
            VALUES (?, ?, ?, ?);
            """, (record.id, record.name, steps_json, record.created_at))
            conn.commit()
        return record

    def get_workflow(self, name: str) -> Optional[WorkflowRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflows WHERE name = ? OR name LIKE ?;", (name.lower(), f"%{name.lower()}%"))
            row = cursor.fetchone()
            if row:
                steps_data = json.loads(row["steps"])
                steps_objs = [WorkflowStep(**s) for s in steps_data]
                return WorkflowRecord(
                    id=row["id"],
                    name=row["name"],
                    steps=steps_objs,
                    created_at=row["created_at"]
                )
        return None

    def list_workflows(self) -> List[WorkflowRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflows ORDER BY created_at DESC;")
            rows = cursor.fetchall()
            workflows = []
            for row in rows:
                steps_data = json.loads(row["steps"])
                workflows.append(WorkflowRecord(
                    id=row["id"],
                    name=row["name"],
                    steps=[WorkflowStep(**s) for s in steps_data],
                    created_at=row["created_at"]
                ))
            return workflows
