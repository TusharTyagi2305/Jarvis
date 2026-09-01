import logging
import threading
from typing import Optional, Callable
from jarvis.config import settings

logger = logging.getLogger("jarvis.hotkey")

class GlobalHotkeyManager:
    """
    Global Keyboard Shortcut Listener for Windows (default: Ctrl + Space).
    Pressing the hotkey activates voice command listening instantly without wake word.
    """

    def __init__(self, hotkey: Optional[str] = None, on_trigger: Optional[Callable] = None):
        self.hotkey = hotkey or settings.global_hotkey
        self.on_trigger = on_trigger
        self._is_running = False

    def start(self):
        try:
            import keyboard
            self._is_running = True

            def _on_hotkey():
                logger.info(f"Global hotkey '{self.hotkey}' triggered.")
                if self.on_trigger:
                    self.on_trigger()
                else:
                    self._default_trigger()

            keyboard.add_hotkey(self.hotkey, _on_hotkey, suppress=False)
            logger.info(f"Global hotkey listener registered for '{self.hotkey}'.")
            return True
        except Exception as e:
            logger.warning(f"Failed to register global hotkey '{self.hotkey}': {e}")
            return False

    def _default_trigger(self):
        try:
            import urllib.request
            req = urllib.request.Request(
                f"http://{settings.api_host}:{settings.api_port}/api/voice/listen",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception as e:
            logger.warning(f"Failed to send hotkey voice trigger: {e}")

    def stop(self):
        if self._is_running:
            try:
                import keyboard
                keyboard.remove_hotkey(self.hotkey)
            except Exception:
                pass
            self._is_running = False
