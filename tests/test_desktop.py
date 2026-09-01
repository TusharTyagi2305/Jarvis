import pytest
from jarvis.config import settings
from jarvis.desktop import JarvisDesktopApp
from jarvis.tray import JarvisTrayIcon
from jarvis.hotkey import GlobalHotkeyManager
from jarvis.voice.background import BackgroundVoiceListener

def test_desktop_config():
    assert settings.jarvis_floating_mode is True
    assert settings.jarvis_always_on_top is False
    assert settings.global_hotkey == "ctrl+space"
    assert settings.jarvis_desktop_wrapper == "pywebview"

def test_desktop_app_instantiation():
    app = JarvisDesktopApp(target_url="http://127.0.0.1:5173/")
    assert app.target_url == "http://127.0.0.1:5173/"
    assert app.is_always_on_top is False
    tog = app.toggle_always_on_top()
    assert tog is True

def test_tray_icon_instantiation():
    tray = JarvisTrayIcon()
    assert tray.is_always_on_top is False
    assert tray.is_voice_enabled is True
    img = tray._create_default_image()
    assert img is not None
    assert img.size == (64, 64)

def test_global_hotkey_manager():
    mgr = GlobalHotkeyManager(hotkey="ctrl+space")
    assert mgr.hotkey == "ctrl+space"
    assert mgr._is_running is False

def test_background_voice_listener():
    bg = BackgroundVoiceListener()
    assert bg.detector is not None
    assert bg._is_running is False
    bg.pause_for_tts()
    assert bg._is_paused_for_tts is True
    bg.resume_after_tts()
    assert bg._is_paused_for_tts is False
