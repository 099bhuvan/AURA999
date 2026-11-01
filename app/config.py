import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_default_data_dir() -> Path:
    """Return platform-appropriate persistent application data directory."""
    custom_dir = os.getenv("AURA_DATA_DIR")
    if custom_dir:
        path = Path(custom_dir).expanduser().resolve()
    elif sys.platform == "win32":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            path = Path(local_app_data) / "AURA"
        else:
            path = Path.home() / "AppData" / "Local" / "AURA"
    else:
        path = Path.home() / ".aura"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class AppConfig:
    """Core configuration for AURA application."""
    # Assistant
    assistant_name: str = os.getenv("AURA_ASSISTANT_NAME", "AURA")
    default_greeting: str = "Systems online. How may I assist you today?"
    
    # Storage Paths
    data_dir: Path = field(default_factory=get_default_data_dir)
    db_path: Path = field(init=False)
    notes_dir: Path = field(init=False)
    docs_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    
    # AI Providers
    ai_mode: str = os.getenv("AI_DEFAULT_MODE", "automatic").lower()  # automatic, offline, online
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    online_api_key: str = os.getenv("ONLINE_API_KEY", "")
    online_base_url: str = os.getenv("ONLINE_API_BASE_URL", "https://api.openai.com/v1")
    online_model: str = os.getenv("ONLINE_MODEL_NAME", "gpt-4o-mini")
    
    # Voice & Audio
    voice_enabled: bool = os.getenv("VOICE_ENABLED", "true").lower() in ("true", "1", "yes")
    speech_rate: int = int(os.getenv("SPEECH_RATE", "175"))
    speech_volume: float = float(os.getenv("SPEECH_VOLUME", "1.0"))
    
    # Visuals & Motion
    reduced_motion: bool = os.getenv("REDUCED_MOTION", "false").lower() in ("true", "1", "yes")
    
    # Automation
    automation_enabled: bool = os.getenv("AUTOMATION_ENABLED", "true").lower() in ("true", "1", "yes")
    automation_require_confirmation: bool = os.getenv("AUTOMATION_REQUIRE_CONFIRMATION", "true").lower() in ("true", "1", "yes")

    def __post_init__(self):
        self.db_path = self.data_dir / "aura.db"
        self.notes_dir = self.data_dir / "notes"
        self.docs_dir = self.data_dir / "documents"
        self.logs_dir = self.data_dir / "logs"
        
        # Ensure subdirectories exist
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Global singleton instance
config = AppConfig()
