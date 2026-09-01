import math
import logging
from typing import List, Tuple
from jarvis.memory.models import MemoryRecord

logger = logging.getLogger("jarvis.memory.vector")

class VectorMemoryProvider:
    """
    Local TF-IDF & Cosine Similarity vector search provider for semantic memory retrieval.
    """

    def __init__(self):
        pass

    def _tokenize(self, text: str) -> List[str]:
        import re
        return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 2]

    def _vectorize(self, tokens: List[str]) -> dict:
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        return tf

    def _cosine_similarity(self, vec1: dict, vec2: dict) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def search_semantic(self, query: str, records: List[MemoryRecord], limit: int = 5) -> List[Tuple[MemoryRecord, float]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or not records:
            return []

        query_vec = self._vectorize(query_tokens)
        scored = []

        for r in records:
            rec_tokens = self._tokenize(r.content)
            rec_vec = self._vectorize(rec_tokens)
            sim = self._cosine_similarity(query_vec, rec_vec)
            if sim > 0.1:
                scored.append((r, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]
