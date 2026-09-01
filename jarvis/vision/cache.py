import hashlib
import time
import logging
from typing import Optional, Dict, Any
from PIL import Image
from jarvis.vision.models import ScreenAnalysis

logger = logging.getLogger("jarvis.vision.cache")

class VisionCache:
    """
    Caches screen analysis results based on MD5 image hashes to avoid redundant vision API calls.
    """

    def __init__(self, ttl_seconds: int = 15):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _hash_image(self, image: Image.Image) -> str:
        return hashlib.md5(image.tobytes()).hexdigest()

    def get(self, image: Image.Image) -> Optional[ScreenAnalysis]:
        img_hash = self._hash_image(image)
        entry = self._cache.get(img_hash)
        if entry:
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                logger.info("Vision Cache HIT")
                return entry["analysis"]
            else:
                del self._cache[img_hash]
        return None

    def set(self, image: Image.Image, analysis: ScreenAnalysis):
        img_hash = self._hash_image(image)
        self._cache[img_hash] = {
            "analysis": analysis,
            "timestamp": time.time()
        }

    def clear(self):
        self._cache.clear()
