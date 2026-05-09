from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any

class ISettings(ABC):
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any):
        pass

    @abstractmethod
    def save(self):
        pass

class IMetadataProcessor(ABC):
    @abstractmethod
    def process(self, info: Dict[str, Any], output_folder: str, audio_format: str) -> str:
        """Process metadata and return the new filename (without extension)."""
        pass

class IDownloader(ABC):
    @abstractmethod
    def download(self, url: str, settings: ISettings, progress_hook: Optional[Callable] = None):
        pass
