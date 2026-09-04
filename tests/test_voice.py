import pytest
from jarvis.voice.base import MicState, Transcript
from jarvis.voice.stt import MockSTTProvider
from jarvis.voice.tts import MockTTSProvider
from jarvis.voice.wake_word import KeywordWakeWordDetector
from jarvis.voice.manager import VoiceManager
from jarvis.brain.mock import MockLLMProvider
from jarvis.tools import create_default_registry
from jarvis.security.permissions import PermissionEngine
from jarvis.security.audit import AuditLogger
from jarvis.orchestrator.agent_loop import JarvisOrchestrator

def test_stt_provider():
    stt = MockSTTProvider(preset_transcript="Jarvis, open Notepad")
    res = stt.transcribe()
    assert res.text == "Jarvis, open Notepad"
    assert res.confidence == 0.98

def test_tts_provider():
    tts = MockTTSProvider()
    res = tts.speak("Notepad is open.")
    assert res is True
    assert "Notepad is open." in tts.spoken_history

def test_wake_word_detector():
    detector = KeywordWakeWordDetector(keyword="jarvis")
    assert detector.detect("Jarvis") is True
    assert detector.detect("jarvis") is True
    assert detector.detect("JARVIS") is True
    assert detector.detect("Hey Jarvis, what is the battery level?") is True
    assert detector.detect("jarvis please open youtube") is True
    assert detector.detect("ok jarvis search google") is True
    assert detector.detect("okay jarvis search youtube") is True
    assert detector.detect("Hello world") is False
    assert detector.detect("Hey Alexa, open Notepad") is False
    assert detector.detect("alexa") is False

def test_mic_state_enum():
    assert MicState.DISABLED.value == "DISABLED"
    assert MicState.PERMISSION_REQUIRED.value == "PERMISSION_REQUIRED"

def test_voice_manager_execution_cycle(tmp_path):
    audit_logger = AuditLogger(log_dir=tmp_path / "logs")
    orchestrator = JarvisOrchestrator(
        llm_provider=MockLLMProvider(),
        tool_registry=create_default_registry(),
        permission_engine=PermissionEngine(),
        audit_logger=audit_logger
    )

    stt = MockSTTProvider(preset_transcript="Bharu, check battery")
    tts = MockTTSProvider()
    detector = KeywordWakeWordDetector(keyword="bharu")

    manager = VoiceManager(
        orchestrator=orchestrator,
        stt_provider=stt,
        tts_provider=tts,
        wake_word_detector=detector
    )

def test_background_listener_diagnostics_and_device_resolution():
    from jarvis.voice.background import BackgroundVoiceListener
    bg = BackgroundVoiceListener()
    diag = bg.get_diagnostics()
    assert "device" in diag
    assert "energy_threshold" in diag
    assert "state" in diag
    assert diag["is_running"] is False

    class MockSD:
        class default:
            device = [0, 1]

        @staticmethod
        def query_devices(index=None, kind=None):
            devs = [
                {"name": "Default Audio", "max_input_channels": 2},
                {"name": "Realtek High Definition Audio Mic", "max_input_channels": 2},
                {"name": "USB Headset Mic", "max_input_channels": 2}
            ]
            if index is not None:
                return devs[index]
            return devs

    idx = bg.resolve_sounddevice_input_device(MockSD)
    assert idx == 0

    bg.selected_device_name = "default"
    from jarvis.config import settings
    original_device = settings.voice_input_device
    try:
        settings.voice_input_device = "Realtek"
        idx = bg.resolve_sounddevice_input_device(MockSD)
        assert idx == 1
        assert "Realtek" in bg.selected_device_name
    finally:
        settings.voice_input_device = original_device

def test_inline_wake_command_parsing():
    from jarvis.voice.background import BackgroundVoiceListener
    bg = BackgroundVoiceListener()

    clean_cmd = ""
    transcript = "Bharu, open YouTube and search hasmob002"
    for kw in ["bharu", "hey bharu", "bharu please", "ok bharu", "okay bharu"]:
        if kw in transcript.lower():
            idx = transcript.lower().find(kw)
            rem = transcript[idx + len(kw):].strip(", ").strip()
            if rem:
                clean_cmd = rem
                break
    assert clean_cmd == "open YouTube and search hasmob002"
