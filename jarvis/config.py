import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    llm_model: str = Field(default="gemini-2.5-flash", validation_alias="LLM_MODEL")
    max_agent_iterations: int = Field(default=10, validation_alias="MAX_AGENT_ITERATIONS")
    default_auto_confirm_safe: bool = Field(default=True, validation_alias="DEFAULT_AUTO_CONFIRM_SAFE")
    workspace_dir: Path = Field(
        default_factory=lambda: Path(os.getcwd()).resolve(),
        validation_alias="SAFE_WORKING_DIRECTORY"
    )

    # Network & API settings
    api_host: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")
    frontend_host: str = Field(default="127.0.0.1", validation_alias="FRONTEND_HOST")
    frontend_port: int = Field(default=5173, validation_alias="FRONTEND_PORT")
    browser_headless: bool = Field(default=False, validation_alias="BROWSER_HEADLESS")

    # Voice & Language settings
    voice_enabled: bool = Field(default=True, validation_alias="VOICE_ENABLED")
    wake_word_enabled: bool = Field(default=True, validation_alias="WAKE_WORD_ENABLED")
    wake_word: str = Field(default="jarvis", validation_alias="WAKE_WORD")
    stt_provider: str = Field(default="native", validation_alias="STT_PROVIDER")
    tts_provider: str = Field(default="native", validation_alias="TTS_PROVIDER")
    voice_language: str = Field(default="hi-IN", validation_alias="VOICE_LANGUAGE")
    jarvis_language: str = Field(default="hi-IN", validation_alias="JARVIS_LANGUAGE")
    jarvis_secondary_language: str = Field(default="en-IN", validation_alias="JARVIS_SECONDARY_LANGUAGE")
    jarvis_auto_language_detection: bool = Field(default=True, validation_alias="JARVIS_AUTO_LANGUAGE_DETECTION")
    jarvis_debug_mode: bool = Field(default=False, validation_alias="JARVIS_DEBUG_MODE")
    voice_timeout_seconds: int = Field(default=8, validation_alias="VOICE_TIMEOUT_SECONDS")
    conversation_timeout_seconds: int = Field(default=8, validation_alias="CONVERSATION_TIMEOUT_SECONDS")
    voice_input_device: str = Field(default="default", validation_alias="VOICE_INPUT_DEVICE")
    voice_energy_threshold: int = Field(default=80, validation_alias="VOICE_ENERGY_THRESHOLD")
    voice_dynamic_energy: bool = Field(default=True, validation_alias="VOICE_DYNAMIC_ENERGY")
    voice_ambient_calibration_seconds: float = Field(default=1.5, validation_alias="VOICE_AMBIENT_CALIBRATION_SECONDS")
    voice_debug: bool = Field(default=True, validation_alias="VOICE_DEBUG")
    voice_conversation_mode: bool = Field(default=True, validation_alias="VOICE_CONVERSATION_MODE")
    voice_conversation_timeout_seconds: int = Field(default=25, validation_alias="VOICE_CONVERSATION_TIMEOUT_SECONDS")
    jarvis_debug_pipeline: bool = Field(default=True, validation_alias="JARVIS_DEBUG_PIPELINE")

    # Vision settings
    vision_enabled: bool = Field(default=True, validation_alias="VISION_ENABLED")
    vision_provider: str = Field(default="gemini", validation_alias="VISION_PROVIDER")
    vision_model: str = Field(default="gemini-2.5-flash", validation_alias="VISION_MODEL")
    vision_click_confidence_threshold: float = Field(default=0.85, validation_alias="VISION_CLICK_CONFIDENCE_THRESHOLD")
    vision_max_image_size: int = Field(default=1280, validation_alias="VISION_MAX_IMAGE_SIZE")

    # Memory settings
    memory_enabled: bool = Field(default=True, validation_alias="MEMORY_ENABLED")
    semantic_memory_enabled: bool = Field(default=True, validation_alias="SEMANTIC_MEMORY_ENABLED")
    allow_automatic_memory: bool = Field(default=False, validation_alias="ALLOW_AUTOMATIC_MEMORY")
    memory_max_results: int = Field(default=5, validation_alias="MEMORY_MAX_RESULTS")
    memory_db_path: str = Field(default="data/memory/jarvis_memory.db", validation_alias="MEMORY_DB_PATH")

    # Task planning settings
    max_task_steps: int = Field(default=30, validation_alias="MAX_TASK_STEPS")
    max_step_retries: int = Field(default=2, validation_alias="MAX_STEP_RETRIES")
    max_agent_iterations: int = Field(default=50, validation_alias="MAX_AGENT_ITERATIONS")
    max_task_duration_seconds: int = Field(default=1800, validation_alias="MAX_TASK_DURATION_SECONDS")

    # Production & Startup settings
    jarvis_version: str = Field(default="1.0.0", validation_alias="JARVIS_VERSION")
    jarvis_start_with_windows: bool = Field(default=False, validation_alias="JARVIS_START_WITH_WINDOWS")
    jarvis_start_minimized: bool = Field(default=False, validation_alias="JARVIS_START_MINIMIZED")
    jarvis_background_mode: bool = Field(default=True, validation_alias="JARVIS_BACKGROUND_MODE")
    jarvis_auto_open_dashboard: bool = Field(default=True, validation_alias="JARVIS_AUTO_OPEN_DASHBOARD")
    jarvis_floating_mode: bool = Field(default=True, validation_alias="JARVIS_FLOATING_MODE")
    jarvis_always_on_top: bool = Field(default=False, validation_alias="JARVIS_ALWAYS_ON_TOP")
    global_hotkey: str = Field(default="ctrl+space", validation_alias="GLOBAL_HOTKEY")
    jarvis_desktop_wrapper: str = Field(default="pywebview", validation_alias="JARVIS_DESKTOP_WRAPPER")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
