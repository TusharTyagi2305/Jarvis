import os
import sys
import time
import socket
import logging
import subprocess
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

from jarvis.config import settings
from jarvis.utils.paths import get_app_data_dir

logger = logging.getLogger("jarvis.launcher")

class JarvisLauncher:
    """
    One-Click Production Launcher managing PID locking, backend/frontend process lifecycle,
    PowerShell npm.cmd compatibility, health polling, and clean shutdown.
    """

    def __init__(self):
        self.base_dir = get_app_data_dir()
        self.pid_file = self.base_dir / "scratch" / "jarvis.pid"
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.tray_icon = None
        self.hotkey_mgr = None
        self.bg_voice = None
        self.desktop_app = None

    def is_already_running(self) -> bool:
        if not self.pid_file.exists():
            return False
        try:
            pid = int(self.pid_file.read_text().strip())
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                SYNCHRONIZE = 0x00100000
                process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
                if process:
                    kernel32.CloseHandle(process)
                    return True
            else:
                os.kill(pid, 0)
                return True
        except Exception:
            pass
        return False

    def acquire_pid_lock(self):
        if self.is_already_running():
            logger.error("JARVIS is already running. Duplicate launcher execution blocked.")
            raise RuntimeError("JARVIS is already running.")
        self.pid_file.write_text(str(os.getpid()))

    def release_pid_lock(self):
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except Exception:
                pass

    def is_port_in_use(self, host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex((host, port)) == 0

    def start_backend(self) -> bool:
        if self.is_port_in_use(settings.api_host, settings.api_port):
            # Check if existing backend is healthy
            if self._wait_for_health(timeout_seconds=2):
                logger.info("Backend is already running and healthy. Reusing existing instance.")
                return True

        logger.info("Starting JARVIS FastAPI backend service...")
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        cmd = [sys.executable, "-m", "jarvis.api.app"]
        self.backend_process = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self._wait_for_health(timeout_seconds=25)

    def _wait_for_health(self, timeout_seconds: int = 15) -> bool:
        url = f"http://{settings.api_host}:{settings.api_port}/health"
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                req = urllib.request.urlopen(url, timeout=1)
                if req.status == 200:
                    logger.info("Backend health check PASSED.")
                    return True
            except Exception:
                time.sleep(0.5)
        logger.warning("Backend health check timeout.")
        return False

    def start_frontend(self) -> bool:
        """
        Starts frontend dev server using npm.cmd on Windows to bypass PowerShell script execution restrictions.
        Detects if port 5173 is already running.
        """
        import shutil
        frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

        # Check if frontend port is already active
        if self.is_port_in_use(settings.frontend_host, settings.frontend_port):
            if self._wait_for_frontend_health(timeout_seconds=2):
                logger.info("Frontend is already running and accessible. Reusing existing instance.")
                return True

        logger.info("Starting JARVIS React/Vite frontend...")

        if sys.platform == "win32":
            npm_bin = shutil.which("npm.cmd") or "npm.cmd"
            cmd = [npm_bin, "run", "dev"]
            use_shell = True
        else:
            cmd = ["npm", "run", "dev"]
            use_shell = False

        try:
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=frontend_dir,
                shell=use_shell,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as ex:
            logger.error(f"Failed to launch frontend process: {ex}")
            return False

        return self._wait_for_frontend_health()

    def _wait_for_frontend_health(self, timeout_seconds: int = 20) -> bool:
        url = f"http://{settings.frontend_host}:{settings.frontend_port}/"
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                req = urllib.request.urlopen(url, timeout=1)
                if req.status in (200, 304):
                    logger.info("Frontend health check PASSED.")
                    return True
            except Exception:
                time.sleep(0.5)
        logger.warning("Frontend health check timeout.")
        return False

        self.tray_icon = None
        self.hotkey_mgr = None
        self.bg_voice = None
        self.desktop_app = None

    def start_all(self, run_desktop_block: bool = True) -> bool:
        """
        Full 1-Click Desktop Startup Sequence:
        1. Acquire PID lock
        2. Start Backend & verify health
        3. Start Frontend & verify health
        4. Start System Tray Icon
        5. Start Global Hotkey (Ctrl + Space)
        6. Start Background Voice Listener ("Jarvis")
        7. Open Native PyWebView Desktop HUD Window
        """
        self.acquire_pid_lock()
        print(f"Starting JARVIS v{settings.jarvis_version} Desktop System...\n")

        print("Backend starting...")
        if not self.start_backend():
            print("Backend startup failed.")
            return False
        print("Backend healthy...\n")

        print("Frontend starting...")
        if not self.start_frontend():
            print("Frontend startup failed.")
            return False
        print("Frontend healthy...\n")

        # 4. System Tray Icon
        try:
            from jarvis.tray import JarvisTrayIcon
            self.tray_icon = JarvisTrayIcon(
                on_open=lambda: self.desktop_app.show() if self.desktop_app else None,
                on_exit=lambda: self.stop_all()
            )
            self.tray_icon.start(block=False)
            print("System Tray Icon active...\n")
        except Exception as e:
            logger.warning(f"Could not start System Tray Icon: {e}")

        # 5. Global Keyboard Shortcut
        try:
            from jarvis.hotkey import GlobalHotkeyManager
            self.hotkey_mgr = GlobalHotkeyManager()
            self.hotkey_mgr.start()
            print(f"Global Hotkey active ({settings.global_hotkey})...\n")
        except Exception as e:
            logger.warning(f"Could not start Global Hotkey Manager: {e}")

        # 6. Background Voice Listener
        try:
            from jarvis.voice.background import BackgroundVoiceListener
            self.bg_voice = BackgroundVoiceListener()
            self.bg_voice.start()
            print("Background Voice Listener active ('Jarvis')...\n")
        except Exception as e:
            logger.warning(f"Could not start Background Voice Listener: {e}")

        # 7. Native Desktop HUD Window
        try:
            from jarvis.desktop import JarvisDesktopApp
            self.desktop_app = JarvisDesktopApp()
            print("Opening JARVIS Native Desktop HUD Window...")
            if run_desktop_block:
                self.desktop_app.start(block=True)
            else:
                self.desktop_app.start(block=False)
            print("\nJARVIS Desktop System is ready.")
            return True
        except Exception as e:
            logger.error(f"Failed to start Desktop HUD Window: {e}")
            webbrowser.open(f"http://{settings.frontend_host}:{settings.frontend_port}/")
            return True

    def stop_all(self):
        logger.info("Shutting down JARVIS Desktop System cleanly...")

        if self.bg_voice:
            try:
                self.bg_voice.stop()
            except Exception:
                pass
            self.bg_voice = None

        if self.hotkey_mgr:
            try:
                self.hotkey_mgr.stop()
            except Exception:
                pass
            self.hotkey_mgr = None

        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None

        if self.desktop_app:
            try:
                self.desktop_app.close()
            except Exception:
                pass
            self.desktop_app = None

        if self.frontend_process:
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.frontend_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    self.frontend_process.terminate()
                    self.frontend_process.wait(timeout=3)
            except Exception:
                pass
            self.frontend_process = None

        if self.backend_process:
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.backend_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    self.backend_process.terminate()
                    self.backend_process.wait(timeout=3)
            except Exception:
                pass
            self.backend_process = None

        self.release_pid_lock()
        logger.info("JARVIS Desktop System shutdown complete.")

if __name__ == "__main__":
    launcher = JarvisLauncher()
    try:
        if launcher.start_all():
            print("Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping JARVIS...")
    finally:
        launcher.stop_all()
