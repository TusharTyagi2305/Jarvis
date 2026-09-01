import logging
from typing import List, Optional
from jarvis.memory.models import MemoryRecord
from jarvis.memory.providers.sqlite import SQLiteMemoryRepository
from jarvis.memory.providers.vector import VectorMemoryProvider

logger = logging.getLogger("jarvis.memory.retrieval")

class MemoryRetriever:
    """
    Ranks, deduplicates, and retrieves relevant memory records for agent prompt context injection.
    """

    def __init__(self, repo: SQLiteMemoryRepository, vector_provider: Optional[VectorMemoryProvider] = None):
        self.repo = repo
        self.vector = vector_provider or VectorMemoryProvider()

    def retrieve(self, query: str, limit: int = 5) -> List[MemoryRecord]:
        if not query or not query.strip():
            return []

        # 1. Structured SQL search
        sql_results = self.repo.search_memories(query=query, limit=limit * 2)

        # 2. Semantic vector ranking
        all_records = self.repo.search_memories(limit=50)
        semantic_results = self.vector.search_semantic(query, all_records, limit=limit)

        # Deduplicate and combine results
        seen_ids = set()
        combined: List[MemoryRecord] = []

        for r, score in semantic_results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                combined.append(r)

        for r in sql_results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                combined.append(r)

        return combined[:limit]

    def format_context_for_prompt(self, records: List[MemoryRecord]) -> str:
        if not records:
            return ""

        lines = ["=== RELEVANT USER MEMORIES & PREFERENCES ==="]
        for idx, r in enumerate(records, 1):
            lines.append(f"{idx}. [{r.category.upper()}] {r.content}")
        lines.append("==========================================")
        return "\n".join(lines)
