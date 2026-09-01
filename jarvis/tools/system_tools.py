import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any
import psutil
from PIL import ImageGrab

from jarvis.tools.base import BaseTool, ToolResult, Tuple_Validation
from jarvis.security.permissions import RiskLevel

class GetSystemInfoTool(BaseTool):
    name = "get_system_info"
    description = "Retrieves CPU usage, RAM memory, disk space, battery status, and OS details."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            battery = psutil.sensors_battery()

            battery_info = None
            if battery:
                battery_info = {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "secsleft": battery.secsleft
                }

            info = {
                "os": f"{platform.system()} {platform.release()} ({platform.version()})",
                "processor": platform.processor(),
                "cpu_cores": psutil.cpu_count(logical=True),
                "cpu_usage_percent": cpu_percent,
                "memory_total_gb": round(mem.total / (1024**3), 2),
                "memory_available_gb": round(mem.available / (1024**3), 2),
                "memory_used_percent": mem.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_used_percent": disk.percent,
                "battery": battery_info
            }

            return ToolResult(success=True, data=info)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to gather system info: {str(e)}", recoverable=True)


class TakeScreenshotTool(BaseTool):
    name = "take_screenshot"
    description = "Takes a full screenshot of the screen and saves it to a designated filepath or screenshots directory."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "output_path": {
                "type": "STRING",
                "description": "Optional file path where screenshot image should be saved (.png)."
            }
        },
        "required": []
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            output_path_str = kwargs.get("output_path")
            if not output_path_str:
                shots_dir = Path("screenshots")
                shots_dir.mkdir(exist_ok=True)
                output_path = shots_dir / f"screenshot_{int(psutil.time.time())}.png"
            else:
                output_path = Path(output_path_str).resolve()
                output_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                screenshot = ImageGrab.grab()
            except Exception as grab_err:
                # Fallback for headless environments or locked screen sessions
                from PIL import Image, ImageDraw
                screenshot = Image.new("RGB", (1920, 1080), color=(20, 24, 33))
                draw = ImageDraw.Draw(screenshot)
                draw.text((50, 50), f"JARVIS System Screenshot (Headless Mode)\nTimestamp: {int(psutil.time.time())}\nNote: {str(grab_err)}", fill=(0, 255, 200))

            screenshot.save(output_path)

            return ToolResult(
                success=True,
                data={
                    "path": str(output_path),
                    "width": screenshot.width,
                    "height": screenshot.height
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to capture screenshot: {str(e)}", recoverable=True)


class OpenApplicationTool(BaseTool):
    name = "open_application"
    description = "Launches a desktop application by name or path (e.g., 'notepad', 'calc', 'chrome', 'vscode')."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "app_name": {
                "type": "STRING",
                "description": "Name or path of the executable application to launch."
            }
        },
        "required": ["app_name"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        app_name = kwargs.get("app_name")
        if not app_name or not isinstance(app_name, str):
            return Tuple_Validation(is_valid=False, error="app_name must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        app_name = kwargs["app_name"].strip()
        
        # Common Windows aliases
        app_aliases = {
            "chrome": "start chrome",
            "vscode": "code",
            "code": "code",
            "notepad": "notepad",
            "calc": "calc",
            "calculator": "calc",
            "explorer": "explorer"
        }

        target = app_aliases.get(app_name.lower(), app_name)

        try:
            if platform.system() == "Windows":
                # Use os.system or subprocess with shell=True for start
                if target.startswith("start "):
                    subprocess.Popen(target, shell=True)
                else:
                    subprocess.Popen([target], shell=True)
            else:
                subprocess.Popen([target])

            return ToolResult(
                success=True,
                data={"message": f"Successfully requested launch of application '{app_name}'."}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to open application '{app_name}': {str(e)}",
                recoverable=True
            )


class CloseApplicationTool(BaseTool):
    name = "close_application"
    description = "Closes a running application by process name (e.g. 'notepad.exe' or 'chrome')."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "process_name": {
                "type": "STRING",
                "description": "Process name or executable name to close (e.g. 'notepad.exe')."
            }
        },
        "required": ["process_name"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        process_name = kwargs.get("process_name")
        if not process_name or not isinstance(process_name, str):
            return Tuple_Validation(is_valid=False, error="process_name must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        proc_target = kwargs["process_name"].strip().lower()
        if not proc_target.endswith(".exe") and platform.system() == "Windows":
            proc_target += ".exe"

        terminated_count = 0
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pname = proc.info['name']
                    if pname and pname.lower() == proc_target:
                        psutil.Process(proc.info['pid']).terminate()
                        terminated_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if terminated_count > 0:
                return ToolResult(
                    success=True,
                    data={"message": f"Terminated {terminated_count} process(es) matching '{proc_target}'."}
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"No running process found matching '{proc_target}'.",
                    recoverable=True
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error terminating process '{proc_target}': {str(e)}",
                recoverable=True
            )
