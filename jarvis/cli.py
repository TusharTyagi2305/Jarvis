import sys
import argparse
import urllib.request
import json
from jarvis.config import settings
from jarvis.diagnostics import StartupDiagnostics

def main():
    parser = argparse.ArgumentParser(prog="jarvis", description="JARVIS Personal Desktop AI Assistant CLI")
    parser.add_argument("command", choices=["status", "start", "stop", "pause", "resume", "health", "logs", "version"], help="CLI command to execute")

    args = parser.parse_args()

    if args.command == "version":
        print(f"JARVIS v{settings.jarvis_version}")

    elif args.command == "health":
        print(f"JARVIS v{settings.jarvis_version}")
        diag = StartupDiagnostics.check_environment()
        for k, v in diag.items():
            if k == "version":
                continue
            status_str = "[READY]" if v else "[DEGRADED]"
            print(f"{k.capitalize():<12} {status_str}")

    elif args.command == "status":
        try:
            req = urllib.request.urlopen(f"http://{settings.api_host}:{settings.api_port}/health", timeout=2)
            if req.status == 200:
                print(f"JARVIS Backend: ONLINE (v{settings.jarvis_version})")
            else:
                print("JARVIS Backend: OFFLINE")
        except Exception:
            print("JARVIS Backend: OFFLINE")

    elif args.command == "pause":
        try:
            req = urllib.request.Request(f"http://{settings.api_host}:{settings.api_port}/api/task/pause", method="POST")
            urllib.request.urlopen(req, timeout=2)
            print("JARVIS Assistant: PAUSED")
        except Exception as ex:
            print(f"Failed to pause JARVIS: {ex}")

    elif args.command == "resume":
        try:
            req = urllib.request.Request(f"http://{settings.api_host}:{settings.api_port}/api/task/resume", method="POST")
            urllib.request.urlopen(req, timeout=2)
            print("JARVIS Assistant: RESUMED")
        except Exception as ex:
            print(f"Failed to resume JARVIS: {ex}")

    elif args.command == "logs":
        print(f"Logs directory: {settings.memory_db_path}")

    elif args.command == "start":
        from jarvis.launcher import JarvisLauncher
        launcher = JarvisLauncher()
        try:
            if launcher.start_all():
                print("\nPress Ctrl+C to stop.")
                while True:
                    import time
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping JARVIS...")
        except Exception as ex:
            print(f"Start error: {ex}")
        finally:
            launcher.stop_all()

    elif args.command == "stop":
        from jarvis.launcher import JarvisLauncher
        launcher = JarvisLauncher()
        launcher.release_pid_lock()
        print("JARVIS stopped.")

if __name__ == "__main__":
    main()
