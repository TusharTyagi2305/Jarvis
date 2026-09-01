import os
import sys
import threading
import logging
import urllib.request
from typing import Optional, Callable
from jarvis.config import settings

logger = logging.getLogger("jarvis.tray")

class JarvisTrayIcon:
    """
    Windows System Tray Icon Manager using pystray and Pillow.
    Provides tray context menu: Open JARVIS, Hide JARVIS, Always On Top, Voice On/Off, Pause, Settings, Logs, Restart, Exit.
    """

    def __init__(self, on_open: Optional[Callable] = None, on_exit: Optional[Callable] = None):
        self.on_open = on_open
        self.on_exit = on_exit
        self.icon: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self.is_voice_enabled = settings.voice_enabled
        self.is_always_on_top = settings.jarvis_always_on_top
        self.is_paused = False

    def _create_default_image(self):
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (64, 64), (13, 20, 36, 255))
            draw = ImageDraw.Draw(img)
            # Outer cyan glow ring
            draw.ellipse([4, 4, 60, 60], outline=(0, 243, 255, 255), width=4)
            # Inner circle
            draw.ellipse([18, 18, 46, 46], fill=(0, 243, 255, 200), outline=(255, 255, 255, 255), width=2)
            # Center white dot
            draw.ellipse([27, 27, 37, 37], fill=(255, 255, 255, 255))
            return img
        except Exception as e:
            logger.warning(f"Failed to generate PIL image for tray icon: {e}")
            return None

    def start(self, block: bool = False):
        try:
            import pystray
            from pystray import MenuItem as item

            image = self._create_default_image()
            if not image:
                logger.error("Could not create image for system tray icon.")
                return False

            menu = pystray.Menu(
                item("🚀 Open JARVIS", self._action_open, default=True),
                item("👁️ Hide JARVIS", self._action_hide),
                item("📌 Always On Top", self._action_toggle_top, checked=lambda item: self.is_always_on_top),
                item("🎙️ Voice Assistant", self._action_toggle_voice, checked=lambda item: self.is_voice_enabled),
                item("⏸️ Pause Assistant", self._action_toggle_pause, checked=lambda item: self.is_paused),
                item("⚙️ Settings", self._action_open_settings),
                item("📜 View System Status", self._action_status),
                item("❌ Exit JARVIS", self._action_exit)
            )

            self.icon = pystray.Icon("JARVIS", image, f"JARVIS v{settings.jarvis_version}", menu)
            logger.info("System Tray Icon created.")

            if block:
                self.icon.run()
            else:
                self._thread = threading.Thread(target=self.icon.run, daemon=True, name="jarvis_tray_thread")
                self._thread.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start system tray icon: {e}")
            return False

    def _action_open(self, icon, item):
        if self.on_open:
            self.on_open()

    def _action_hide(self, icon, item):
        try:
            from jarvis.desktop import desktop_app
            if desktop_app:
                desktop_app.hide()
        except Exception:
            pass

    def _action_toggle_top(self, icon, item):
        self.is_always_on_top = not self.is_always_on_top
        try:
            from jarvis.desktop import desktop_app
            if desktop_app:
                desktop_app.toggle_always_on_top()
        except Exception:
            pass

    def _action_toggle_voice(self, icon, item):
        self.is_voice_enabled = not self.is_voice_enabled
        logger.info(f"Voice Assistant toggled: {self.is_voice_enabled}")

    def _action_toggle_pause(self, icon, item):
        self.is_paused = not self.is_paused
        endpoint = "pause" if self.is_paused else "resume"
        try:
            req = urllib.request.Request(f"http://{settings.api_host}:{settings.api_port}/api/task/{endpoint}", method="POST")
            urllib.request.urlopen(req, timeout=2)
        except Exception as ex:
            logger.warning(f"Failed to toggle pause/resume via tray: {ex}")

    def _action_open_settings(self, icon, item):
        if self.on_open:
            self.on_open()

    def _action_status(self, icon, item):
        try:
            req = urllib.request.urlopen(f"http://{settings.api_host}:{settings.api_port}/health", timeout=2)
            print(f"Health Status: {req.read().decode('utf-8')}")
        except Exception as ex:
            print(f"Health check error: {ex}")

    def _action_exit(self, icon, item):
        if self.icon:
            self.icon.stop()
        if self.on_exit:
            self.on_exit()

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
