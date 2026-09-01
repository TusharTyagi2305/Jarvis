import re
import logging
from typing import Tuple
from jarvis.config import settings

logger = logging.getLogger("jarvis.memory.policies")

class SensitiveDataFilter:
    """
    Blocks persistence of sensitive data such as passwords, tokens, API keys, credit cards, and private keys.
    """

    PATTERNS = [
        r"(?i)\bpassword\b\s*(?:[:=]|is)\s*\S+",
        r"(?i)\bsecret\b\s*(?:[:=]|is)\s*\S+",
        r"(?i)\bapi[_-]?key\b\s*(?:[:=]|is)\s*\S+",
        r"(?i)\btoken\b\s*(?:[:=]|is)\s*\S+",
        r"(?i)\bbearer\s+[a-zA-Z0-9_\-\.]+",
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b", # Credit card
        r"-----BEGIN\s+PRIVATE\s+KEY-----"
    ]

    @classmethod
    def is_sensitive(cls, text: str) -> Tuple[bool, str]:
        if not text:
            return False, ""

        for pat in cls.PATTERNS:
            if re.search(pat, text):
                logger.warning("Sensitive data detected in memory input. Persistence BLOCKED.")
                return True, "Content contains sensitive credentials/secrets."

        return False, ""


class ConsentPolicy:
    """
    Enforces explicit instruction consent policies.
    """

    @classmethod
    def can_persist(cls, source: str = "explicit_user_instruction") -> bool:
        if source == "explicit_user_instruction":
            return True
        return settings.allow_automatic_memory
