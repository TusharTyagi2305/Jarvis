import logging
from pathlib import Path
from jarvis.utils.paths import get_app_data_dir

logger = logging.getLogger("jarvis.utils.cleanup")

def cleanup_temporary_files() -> int:
    """
    Cleans temporary screenshot images and audio recordings.
    Does NOT touch memory database data/memory/ or user files.
    """
    count = 0
    base_dir = get_app_data_dir()

    temp_dirs = [
        base_dir / "screenshots",
        base_dir / "temp_audio",
        base_dir / "scratch"
    ]

    for d in temp_dirs:
        if d.exists() and d.is_dir():
            for f in d.glob("*"):
                if f.is_file() and not f.name.endswith(".db"):
                    try:
                        f.unlink()
                        count += 1
                    except Exception as ex:
                        logger.debug(f"Failed to remove temp file '{f}': {ex}")

    logger.info(f"Cleaned {count} temporary files.")
    return count
