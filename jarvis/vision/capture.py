import time
import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import pyautogui

logger = logging.getLogger("jarvis.vision.capture")

class ScreenCaptureService:
    """
    Captures Windows desktop screenshots with scaling, active window title detection, and temporary file management.
    """

    def __init__(self, temp_dir: Optional[Path] = None):
        if temp_dir is None:
            temp_dir = Path("scratch/screenshots").resolve()
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_active_window_title(self) -> str:
        try:
            import win32gui
            window = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(window)
            return title if title else "Desktop"
        except Exception:
            return "Windows Desktop"

    def get_screen_size(self) -> Tuple[int, int]:
        return pyautogui.size()

    def capture_screen(self, max_size: int = 1280) -> Tuple[Image.Image, str, str]:
        """
        Captures full desktop screenshot.
        Returns (PIL.Image, screenshot_path_str, active_window_title).
        """
        shot_id = f"shot_{int(time.time()*1000)}"
        file_path = self.temp_dir / f"{shot_id}.png"

        active_title = self.get_active_window_title()
        try:
            img = pyautogui.screenshot()
        except Exception as e:
            logger.warning(f"Screen capture warning (headless environment): {e}. Creating fallback image.")
            img = Image.new("RGB", (1280, 720), color=(20, 20, 35))

        # Save temporary screenshot image
        img.save(str(file_path))

        # Scale image if required for vision model API limits
        width, height = img.size
        if max_size and (width > max_size or height > max_size):
            ratio = min(max_size / width, max_size / height)
            new_size = (int(width * ratio), int(height * ratio))
            img_scaled = img.resize(new_size, Image.Resampling.LANCZOS)
        else:
            img_scaled = img

        logger.info(f"Captured screen '{shot_id}' ({width}x{height}) - Active: '{active_title}'")
        return img_scaled, str(file_path), active_title

    def cleanup_old_screenshots(self, max_age_seconds: int = 300):
        now = time.time()
        for p in self.temp_dir.glob("shot_*.png"):
            try:
                if now - p.stat().st_mtime > max_age_seconds:
                    p.unlink()
            except Exception:
                pass
