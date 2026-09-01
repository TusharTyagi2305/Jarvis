import pytest
from fastapi.testclient import TestClient
from jarvis.api.app import app
from jarvis.diagnostics import StartupDiagnostics
from jarvis.launcher import JarvisLauncher
from jarvis.utils.paths import get_app_data_dir
from jarvis.utils.cleanup import cleanup_temporary_files

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "subsystems" in data

def test_startup_diagnostics():
    diag = StartupDiagnostics.check_environment()
    assert "python" in diag
    assert "version" in diag
    assert diag["python"] is True

def test_launcher_pid_locking(tmp_path):
    launcher = JarvisLauncher()
    launcher.base_dir = tmp_path
    launcher.pid_file = tmp_path / "jarvis.pid"

    assert launcher.is_already_running() is False
    launcher.acquire_pid_lock()
    assert launcher.is_already_running() is True
    launcher.release_pid_lock()
    assert launcher.is_already_running() is False

def test_cleanup_temporary_files():
    cleaned = cleanup_temporary_files()
    assert isinstance(cleaned, int)

def test_app_data_paths():
    p = get_app_data_dir()
    assert p.exists()

def test_launcher_port_in_use():
    launcher = JarvisLauncher()
    # Unused port check
    assert launcher.is_port_in_use("127.0.0.1", 59999) is False

def test_launcher_frontend_health_mock(monkeypatch):
    launcher = JarvisLauncher()
    def mock_urlopen(*args, **kwargs):
        class MockResp:
            status = 200
        return MockResp()
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)
    assert launcher._wait_for_frontend_health(timeout_seconds=1) is True

def test_launcher_backend_health_mock(monkeypatch):
    launcher = JarvisLauncher()
    def mock_urlopen(*args, **kwargs):
        class MockResp:
            status = 200
        return MockResp()
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)
    assert launcher._wait_for_health(timeout_seconds=1) is True

def test_launcher_frontend_port_reuse(monkeypatch):
    launcher = JarvisLauncher()
    monkeypatch.setattr(launcher, "is_port_in_use", lambda h, p: True)
    monkeypatch.setattr(launcher, "_wait_for_frontend_health", lambda timeout_seconds=2: True)
    assert launcher.start_frontend() is True

def test_launcher_backend_port_reuse(monkeypatch):
    launcher = JarvisLauncher()
    monkeypatch.setattr(launcher, "is_port_in_use", lambda h, p: True)
    monkeypatch.setattr(launcher, "_wait_for_health", lambda timeout_seconds=2: True)
    assert launcher.start_backend() is True

def test_launcher_stop_all(tmp_path):
    launcher = JarvisLauncher()
    launcher.base_dir = tmp_path
    launcher.pid_file = tmp_path / "jarvis.pid"
    launcher.acquire_pid_lock()
    assert launcher.pid_file.exists()
    launcher.stop_all()
    assert not launcher.pid_file.exists()

def test_config_localhost_binding():
    from jarvis.config import settings
    assert settings.api_host in ("127.0.0.1", "localhost")
    assert settings.frontend_host in ("127.0.0.1", "localhost")
    assert settings.api_port == 8000
    assert settings.frontend_port == 5173

