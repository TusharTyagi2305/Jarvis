import time
import logging
from typing import Optional, Any, Callable
from jarvis.config import settings
from jarvis.voice.base import MicState, Transcript, BaseSTTProvider, BaseTTSProvider, BaseWakeWordDetector
from jarvis.voice.stt import NativeSTTProvider, MockSTTProvider
from jarvis.voice.tts import NativeTTSProvider, MockTTSProvider
from jarvis.voice.wake_word import KeywordWakeWordDetector
from jarvis.orchestrator.agent_loop import JarvisOrchestrator, AgentResponse

logger = logging.getLogger("jarvis.voice.manager")

class VoiceManager:
    """
    Central orchestrator for Phase 3 voice capabilities:
    Wake word detection, STT transcription, Orchestrator command execution, and TTS response playback.
    """

    def __init__(
        self,
        orchestrator: JarvisOrchestrator,
        stt_provider: Optional[BaseSTTProvider] = None,
        tts_provider: Optional[BaseTTSProvider] = None,
        wake_word_detector: Optional[BaseWakeWordDetector] = None
    ):
        self.orchestrator = orchestrator
        self.stt = stt_provider or (NativeSTTProvider() if settings.stt_provider == "native" else MockSTTProvider())
        self.tts = tts_provider or (NativeTTSProvider() if settings.tts_provider == "native" else MockTTSProvider())
        self.wake_word = wake_word_detector or KeywordWakeWordDetector(keyword=settings.wake_word)
        self.current_state: MicState = MicState.IDLE
        self._is_active = False

    def set_state(self, new_state: MicState):
        self.current_state = new_state
        logger.info(f"Voice State -> {new_state.value}")
        try:
            from jarvis.api.websocket import ws_manager
            from jarvis.api.events import VoiceStateEvent
            ws_manager.broadcast_event_sync(VoiceStateEvent(voice_state=new_state.value))
        except Exception:
            pass

    def handle_wake_word(self, audio_or_text: Any) -> bool:
        """
        Checks if audio or text input triggers the wake word.
        If detected, transitions state and responds 'Yes, sir?'.
        """
        self.set_state(MicState.WAKE_LISTENING)
        detected = self.wake_word.detect(audio_or_text, target_keyword=settings.wake_word)
        if detected:
            self.set_state(MicState.WAKE_DETECTED)
            from jarvis.brain.response_formatter import ResponseFormatter
            self.speak_response(ResponseFormatter.format_wake_response())
            self.set_state(MicState.LISTENING)
            return True
        return False

    def process_voice_command(self, audio_data: Optional[Any] = None, text_override: Optional[str] = None) -> AgentResponse:
        """
        Full voice execution cycle: STT -> Agent -> Execution -> TTS.
        """
        # 1. STT Transcription
        if text_override:
            transcript_obj = Transcript(text=text_override, confidence=1.0, language=settings.voice_language)
        else:
            self.set_state(MicState.TRANSCRIBING)
            transcript_obj = self.stt.transcribe(audio_data, language=settings.voice_language)

        text = transcript_obj.text.strip()
        from jarvis.brain.response_formatter import ResponseFormatter
        if not text:
            self.set_state(MicState.ERROR)
            self.speak_response(ResponseFormatter.format_wake_response())
            self.set_state(MicState.IDLE)
            return AgentResponse(
                user_request="",
                final_response="No speech detected.",
                iterations=0,
                plan=None,
                success=False
            )

        # Broadcast live transcript over WebSocket
        try:
            from jarvis.api.websocket import ws_manager
            from jarvis.api.events import TranscriptEvent
            ws_manager.broadcast_event_sync(TranscriptEvent(text=text, is_final=True))
        except Exception:
            pass

        # Check for wake word prefix if text contains it
        kw = settings.wake_word.lower()
        text_lower = text.lower()
        prefixes = [f"hey {kw}", f"ok {kw}", f"okay {kw}", f"{kw} please", kw]
        for pfx in prefixes:
            if text_lower.startswith(pfx):
                clean_text = text[len(pfx):].strip(", ").strip()
                if not clean_text:
                    self.set_state(MicState.WAKE_DETECTED)
                    wake_resp = ResponseFormatter.format_wake_response(text)
                    self.speak_response(wake_resp)
                    self.set_state(MicState.LISTENING)
                    return AgentResponse(
                        user_request=text,
                        final_response=wake_resp,
                        iterations=0,
                        plan=None,
                        success=True
                    )
                text = clean_text
                break

        # 2. Agent Command Processing
        self.set_state(MicState.PROCESSING)
        agent_resp = self.orchestrator.run(user_request=text)

        # 3. Spoken Response output
        spoken_text = ResponseFormatter.format_final_response(agent_resp.final_response, user_request=text)
        if agent_resp.pending_confirmation:
            spoken_text = f"Action {agent_resp.pending_confirmation['tool_name']} requires confirmation."

        self.speak_response(spoken_text)
        next_state = MicState.WAKE_LISTENING if settings.wake_word_enabled else MicState.IDLE
        self.set_state(next_state)

        return agent_resp

    def speak_response(self, text: str) -> bool:
        """
        Triggers TTS speech playback and emits WebSocket events.
        Pauses background microphone listener during playback to prevent feedback loops.
        """
        self.set_state(MicState.SPEAKING)
        bg_voice = getattr(self, "bg_voice", None)

        try:
            if bg_voice and hasattr(bg_voice, "pause_for_tts"):
                bg_voice.pause_for_tts()

            from jarvis.api.websocket import ws_manager
            from jarvis.api.events import SpeechStartedEvent, SpeechCompletedEvent
            ws_manager.broadcast_event_sync(SpeechStartedEvent(text=text))
            success = self.tts.speak(text)
            ws_manager.broadcast_event_sync(SpeechCompletedEvent())
            return success
        except Exception:
            return self.tts.speak(text)
        finally:
            if bg_voice and hasattr(bg_voice, "resume_after_tts"):
                bg_voice.resume_after_tts()
            next_state = MicState.WAKE_LISTENING if settings.wake_word_enabled else MicState.IDLE
            self.set_state(next_state)

    def interrupt_speech(self):
        """
        Interrupts active speech playback.
        """
        self.tts.cancel()
        self.set_state(MicState.IDLE)
