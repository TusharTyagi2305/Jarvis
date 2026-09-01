import os
import sys
from pathlib import Path

def get_app_data_dir() -> Path:
    """
    Returns application data directory.
    Uses APPDATA/JARVIS if frozen/packaged, otherwise local workspace directory.
    """
    if getattr(sys, "frozen", False):
        appdata = os.getenv("APPDATA", str(Path.home()))
        p = Path(appdata) / "JARVIS"
    else:
        p = Path(__file__).resolve().parent.parent.parent

    p.mkdir(parents=True, exist_ok=True)
    return p

def get_memory_db_path() -> Path:
    p = get_app_data_dir() / "data" / "memory" / "jarvis_memory.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def get_logs_dir() -> Path:
    p = get_app_data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p
