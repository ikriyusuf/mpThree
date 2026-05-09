from typing import Any, Dict
from core.interfaces import ISettings


class SettingsManager(ISettings):
    """
    In-memory settings manager for the application.
    Replaces the old JSON-based desktop configuration.
    """

    def __init__(self):
        self.settings: Dict[str, Any] = {
            "output_folder": "/tmp",
            "ffmpeg_location": None,
            "audio_quality": "192",
            "audio_format": "mp3",
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        self.settings[key] = value

    def save(self):
        # Save is not needed for the web app since settings are ephemeral per
        # request
        pass
