import logging
import threading
from typing import Optional, Any
from jarvis.config import settings

logger = logging.getLogger("jarvis.desktop")

class JarvisDesktopApp:
    """
    Native PyWebView Desktop App Wrapper providing floating HUD window management,
    always-on-top toggle, tray minimization, and desktop controls.
    """

    def __init__(self, target_url: Optional[str] = None):
        self.target_url = target_url or f"http://{settings.frontend_host}:{settings.frontend_port}/"
        self.window: Optional[Any] = None
        self.is_always_on_top = settings.jarvis_always_on_top
        self.is_minimized = settings.jarvis_start_minimized
        self._thread: Optional[threading.Thread] = None

    def start(self, block: bool = False):
        """
        Launches the native pywebview desktop window.
        """
        try:
            import webview

            class DesktopAPI:
                def toggle_always_on_top(self_api, on_top: Optional[bool] = None):
                    if not self.window:
                        return False
                    if on_top is None:
                        self.is_always_on_top = not self.is_always_on_top
                    else:
                        self.is_always_on_top = on_top
                    try:
                        self.window.on_top = self.is_always_on_top
                    except Exception:
                        pass
                    return self.is_always_on_top

                def minimize_to_tray(self_api):
                    if self.window:
                        try:
                            self.window.minimize()
                        except Exception:
                            pass
                    return True

                def hide_window(self_api):
                    if self.window:
                        try:
                            self.window.hide()
                        except Exception:
                            pass
                    return True

                def show_window(self_api):
                    if self.window:
                        try:
                            self.window.show()
                        except Exception:
                            pass
                    return True

                def get_config(self_api):
                    return {
                        "always_on_top": self.is_always_on_top,
                        "floating_mode": settings.jarvis_floating_mode,
                        "global_hotkey": settings.global_hotkey,
                        "version": settings.jarvis_version
                    }

            api = DesktopAPI()
            self.window = webview.create_window(
                title=f"JARVIS Personal AI Desktop System v{settings.jarvis_version}",
                url=self.target_url,
                width=1180,
                height=780,
                resizable=True,
                on_top=self.is_always_on_top,
                js_api=api
            )

            logger.info(f"PyWebView Desktop HUD Window initialized (URL: {self.target_url})")

            if block:
                webview.start()
            else:
                self._thread = threading.Thread(target=webview.start, daemon=True, name="jarvis_pywebview_thread")
                self._thread.start()
            return True

        except Exception as e:
            logger.error(f"Failed to start PyWebView desktop app: {e}")
            return False

    def show(self):
        if self.window:
            try:
                self.window.show()
            except Exception:
                pass

    def hide(self):
        if self.window:
            try:
                self.window.hide()
            except Exception:
                pass

    def toggle_always_on_top(self) -> bool:
        self.is_always_on_top = not self.is_always_on_top
        if self.window:
            try:
                self.window.on_top = self.is_always_on_top
            except Exception:
                pass
        return self.is_always_on_top

    def close(self):
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None
