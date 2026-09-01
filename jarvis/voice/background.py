import time
import logging
import numpy as np
import threading
from typing import Optional, Dict, Any
from jarvis.config import settings
from jarvis.voice.wake_word.detector import KeywordWakeWordDetector

logger = logging.getLogger("jarvis.voice.background")

class BackgroundVoiceListener:
    """
    Continuous Python background wake word listener backed by sounddevice / speech_recognition.
    Features:
    - Persistent real hardware microphone stream
    - Startup 1.5s ambient noise calibration
    - Dynamic energy thresholding
    - Input device selection (VOICE_INPUT_DEVICE)
    - Inline wake command extraction ("Jarvis, open Notepad")
    - Bounded listener error recovery
    - Safe diagnostic reporting (VOICE_DEBUG=true)
    """

    def __init__(self):
        self.detector = KeywordWakeWordDetector(keyword=settings.wake_word)
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._is_paused_for_tts = False
        self.current_state = "STOPPED"
        self.selected_device_name = "System Default Microphone"
        self.selected_device_index: Optional[int] = None
        self.energy_threshold = settings.voice_energy_threshold
        self.ambient_baseline = 0
        self.sample_rate = 16000
        self.consecutive_errors = 0
        self.max_recovery_attempts = 5

    @property
    def state(self) -> str:
        return self.current_state

    def start(self):
        if self._is_running:
            return True
        self._is_running = True
        self.current_state = "STARTING"
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="jarvis_background_voice")
        self._thread.start()
        logger.info("Background Voice Listener thread started.")
        return True

    def pause_for_tts(self):
        self._is_paused_for_tts = True
        if self.current_state not in ("STOPPED", "ERROR"):
            self.current_state = "SPEAKING"

    def resume_after_tts(self):
        self._is_paused_for_tts = False
        if self._is_running and self.current_state != "STOPPED":
            self.current_state = "WAKE_LISTENING"

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "device": self.selected_device_name,
            "device_index": self.selected_device_index,
            "sample_rate": self.sample_rate,
            "energy_threshold": self.energy_threshold,
            "ambient_baseline": self.ambient_baseline,
            "state": self.current_state,
            "is_running": self._is_running,
            "is_paused_for_tts": self._is_paused_for_tts
        }

    def resolve_sounddevice_input_device(self, sd_module) -> Optional[int]:
        dev_setting = settings.voice_input_device.strip()
        try:
            devices = sd_module.query_devices()
            if not dev_setting or dev_setting.lower() == "default":
                default_idx = sd_module.default.device[0]
                if default_idx is not None and default_idx >= 0:
                    info = sd_module.query_devices(default_idx, 'input')
                    self.selected_device_name = info.get('name', 'Default Microphone')
                    self.selected_device_index = default_idx
                    return default_idx

            if dev_setting.isdigit():
                idx = int(dev_setting)
                if 0 <= idx < len(devices):
                    info = sd_module.query_devices(idx, 'input')
                    if info.get('max_input_channels', 0) > 0:
                        self.selected_device_name = info.get('name', f'Device {idx}')
                        self.selected_device_index = idx
                        return idx

            for idx, dev in enumerate(devices):
                if dev.get('max_input_channels', 0) > 0 and dev_setting.lower() in dev.get('name', '').lower():
                    self.selected_device_name = dev.get('name', f'Device {idx}')
                    self.selected_device_index = idx
                    return idx
        except Exception as e:
            logger.warning(f"[VOICE] Error querying sounddevice input devices: {e}")

        self.selected_device_name = "System Default Microphone"
        self.selected_device_index = None
        return None

    def _listen_loop(self):
        try:
            import speech_recognition as sr
            import sounddevice as sd
            has_sounddevice = True
        except ImportError:
            has_sounddevice = False
            try:
                import speech_recognition as sr
            except ImportError:
                logger.error("[VOICE] Speech recognition module unavailable.")
                self.current_state = "ERROR"
                return

        recognizer = sr.Recognizer()

        while self._is_running and self.consecutive_errors < self.max_recovery_attempts:
            try:
                if has_sounddevice:
                    self._listen_loop_sounddevice(sd, sr, recognizer)
                else:
                    self._listen_loop_pyaudio(sr, recognizer)
            except Exception as ex:
                self.consecutive_errors += 1
                self.current_state = "ERROR"
                logger.warning(f"[VOICE] Background listener exception (attempt {self.consecutive_errors}/{self.max_recovery_attempts}): {ex}")
                time.sleep(1.0)

        if self._is_running and self.consecutive_errors >= self.max_recovery_attempts:
            logger.error("[VOICE] Bounded listener recovery exceeded maximum retries. Listener stopped.")
            self.current_state = "ERROR"
            self._is_running = False
        else:
            self.current_state = "STOPPED"

    def _listen_loop_sounddevice(self, sd, sr, recognizer):
        dev_idx = self.resolve_sounddevice_input_device(sd)
        self.sample_rate = 16000

        if settings.voice_debug:
            logger.info(f"[VOICE] Opening sounddevice microphone '{self.selected_device_name}' (index: {dev_idx})...")

        # 1. Startup Ambient Noise Calibration (1.5 seconds)
        self.current_state = "CALIBRATING"
        calib_duration = max(0.5, min(3.0, settings.voice_ambient_calibration_seconds))
        if settings.voice_debug:
            logger.info(f"[VOICE] Measuring ambient noise baseline for {calib_duration}s...")

        try:
            amb_recording = sd.rec(int(calib_duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='int16', device=dev_idx)
            sd.wait()
            rms = float(np.sqrt(np.mean(amb_recording.astype(np.float64) ** 2)))
            self.ambient_baseline = round(rms, 2)
            calculated_thresh = max(150, min(1000, int(rms * 1.25)))
            self.energy_threshold = calculated_thresh
        except Exception as ex:
            logger.warning(f"[VOICE] Ambient calibration recording warning: {ex}")
            self.ambient_baseline = 10
            self.energy_threshold = settings.voice_energy_threshold

        if settings.voice_debug:
            logger.info(f"[VOICE] Ambient RMS Baseline: {self.ambient_baseline} | Energy Threshold: {self.energy_threshold}")
            logger.info(f"[VOICE] State -> WAKE_LISTENING")

        self.current_state = "WAKE_LISTENING"
        self.consecutive_errors = 0

        # 2. Continuous Wake Listening Loop over persistent hardware mic stream
        chunk_duration = 3.5
        chunk_samples = int(chunk_duration * self.sample_rate)

        while self._is_running:
            if self._is_paused_for_tts:
                time.sleep(0.2)
                continue

            # Check if conversation mode is active
            in_conversation_mode = settings.voice_conversation_mode and (time.time() < getattr(self, "conversation_mode_until", 0))
            if in_conversation_mode:
                self.current_state = "LISTENING"

            try:
                rec_data = sd.rec(chunk_samples, samplerate=self.sample_rate, channels=1, dtype='int16', device=dev_idx)
                sd.wait()

                if self._is_paused_for_tts or not self._is_running:
                    time.sleep(0.1)
                    continue

                # Optimized low-overhead audio frame energy calculation
                chunk_rms = float(np.mean(np.abs(rec_data)))
                
                # Check if audio frame energy exceeds baseline threshold
                if chunk_rms >= max(10.0, self.ambient_baseline * 1.05):
                    pcm_bytes = rec_data.tobytes()
                    audio_obj = sr.AudioData(pcm_bytes, self.sample_rate, 2)

                    try:
                        text = recognizer.recognize_google(audio_obj, language=settings.voice_language).strip()
                        if settings.voice_debug:
                            logger.info(f"[VOICE] Captured final transcript: '{text}' (RMS: {chunk_rms:.2f})")

                        # If in active conversation mode or wake word is detected
                        if in_conversation_mode or self.detector.detect(text, target_keyword=settings.wake_word):
                            logger.info(f"[VOICE] COMMAND / WAKE WORD CONFIRMED: '{text}'")
                            self.current_state = "WAKE_DETECTED"
                            self.conversation_mode_until = time.time() + settings.voice_conversation_timeout_seconds
                            self._trigger_wake_action(text)
                            time.sleep(0.5)
                            if self._is_running and not self._is_paused_for_tts:
                                self.current_state = "WAKE_LISTENING"

                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as re:
                        logger.warning(f"[VOICE] STT API request warning: {re}")
                        time.sleep(0.5)

                time.sleep(0.05)

            except Exception as ex:
                logger.warning(f"[VOICE] Sounddevice chunk recording iteration exception: {ex}")
                time.sleep(1.0)
                break

    def _listen_loop_pyaudio(self, sr, recognizer):
        recognizer.dynamic_energy_threshold = settings.voice_dynamic_energy
        recognizer.pause_threshold = 0.5

        with sr.Microphone() as source:
            self.current_state = "CALIBRATING"
            recognizer.adjust_for_ambient_noise(source, duration=settings.voice_ambient_calibration_seconds)
            self.ambient_baseline = int(recognizer.energy_threshold)
            self.energy_threshold = max(150, min(1000, int(self.ambient_baseline * 1.15)))
            recognizer.energy_threshold = self.energy_threshold
            self.current_state = "WAKE_LISTENING"
            self.consecutive_errors = 0

            while self._is_running:
                if self._is_paused_for_tts:
                    time.sleep(0.2)
                    continue

                try:
                    audio = recognizer.listen(source, timeout=2.5, phrase_time_limit=3.5)
                except sr.WaitTimeoutError:
                    continue

                if self._is_paused_for_tts or not self._is_running:
                    continue

                try:
                    text = recognizer.recognize_google(audio, language=settings.voice_language).strip()
                    if self.detector.detect(text, target_keyword=settings.wake_word):
                        logger.info(f"[VOICE] WAKE WORD DETECTED: '{text}'")
                        self.current_state = "WAKE_DETECTED"
                        self._trigger_wake_action(text)
                        time.sleep(0.5)
                        if self._is_running and not self._is_paused_for_tts:
                            self.current_state = "WAKE_LISTENING"
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    time.sleep(0.5)

    def _trigger_wake_action(self, transcript: str):
        try:
            import urllib.request
            import json

            # Inline Command Extraction: "Jarvis, open Notepad" -> "open Notepad"
            clean_cmd = ""
            for kw in ["jarvis", "hey jarvis", "jarvis please", "ok jarvis", "okay jarvis"]:
                if kw in transcript.lower():
                    idx = transcript.lower().find(kw)
                    rem = transcript[idx + len(kw):].strip(", ").strip()
                    if rem:
                        clean_cmd = rem
                        break

            payload = json.dumps({"text_override": clean_cmd if clean_cmd else None}).encode("utf-8")
            req = urllib.request.Request(
                f"http://{settings.api_host}:{settings.api_port}/api/voice/listen",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            logger.warning(f"[VOICE] Failed to send wake action trigger: {e}")

    def stop(self):
        self._is_running = False
        self.current_state = "STOPPED"
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("[VOICE] Background Voice Listener stopped cleanly.")
