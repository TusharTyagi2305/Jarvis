import re
import logging
from jarvis.security.permissions import RiskLevel

logger = logging.getLogger("jarvis.security.terminal")

class TerminalSafetyClassifier:
    """
    Classifies terminal shell commands into LOW (SAFE), MEDIUM (SAFE), or HIGH (CONFIRM/DANGEROUS) risk.
    """

    HIGH_RISK_PATTERNS = [
        r"(?i)\b(?:rm|del|erase|format|diskpart|fdisk|mkfs|dd|shred)\b",
        r"(?i)\b(?:rmdir|rd)\s+/[sS]",
        r"(?i)\b(?:reg|regedit|bcdedit|vssadmin)\b",
        r"(?i)\b(?:chmod\s+777|chown)\b",
        r"(?i)powershell.*-ExecutionPolicy\s+Bypass"
    ]

    MEDIUM_RISK_PATTERNS = [
        r"(?i)\b(?:npm|pip|cargo|go)\s+(?:install|add|uninstall|remove)\b",
        r"(?i)\bgit\s+(?:checkout|reset|clean|pull|rebase)\b"
    ]

    @classmethod
    def classify(cls, command: str) -> RiskLevel:
        if not command or not command.strip():
            return RiskLevel.SAFE

        cmd_clean = command.strip()

        for pat in cls.HIGH_RISK_PATTERNS:
            if re.search(pat, cmd_clean):
                logger.warning(f"Terminal command classified as HIGH risk: '{cmd_clean}'")
                return RiskLevel.CONFIRM

        for pat in cls.MEDIUM_RISK_PATTERNS:
            if re.search(pat, cmd_clean):
                return RiskLevel.SAFE

        return RiskLevel.SAFE
