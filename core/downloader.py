import yt_dlp
import os
from typing import Callable, Optional, Dict, Any
from core.interfaces import IDownloader, ISettings, IMetadataProcessor


class YtDlpDownloader(IDownloader):
    def __init__(self, processor: Optional[IMetadataProcessor] = None):
        self.processor = processor
        self.is_downloading = False

    def build_ydl_options(self,
                          settings: ISettings,
                          progress_hook: Optional[Callable] = None) -> Dict[str, Any]:
        return {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(settings.get("output_folder"), "%(title)s - [%(id)s].%(ext)s"),
            "ffmpeg_location": settings.get("ffmpeg_location"),
            "progress_hooks": [progress_hook] if progress_hook else [],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": settings.get("audio_format"),
                    "preferredquality": settings.get("audio_quality"),
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            "writethumbnail": True,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "postprocessor_args": {
                "EmbedThumbnail": [],
            },
            "no_color": True,
            "socket_timeout": 30,
            "concurrent_fragment_downloads": 4,
            "geo_bypass": True,
            "noplaylist": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "mweb", "web"]
                }
            }
        }

    def download(self, url: str, settings: ISettings,
                 progress_hook: Optional[Callable] = None):
        self.is_downloading = True
        try:
            os.makedirs(settings.get("output_folder"), exist_ok=True)
            ydl_opts = self.build_ydl_options(settings, progress_hook)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise Exception("İndirme başarısız oldu. İlgili URL'den veri alınamadı.")

                # Cleanup/Post-process after download finishes
                if self.processor:
                    if isinstance(info, dict) and info.get("_type") == "playlist":
                        for entry in info.get("entries", []):
                            if entry:
                                self.processor.process(
                                    entry, settings.get("output_folder"), settings.get("audio_format"))
                    else:
                        self.processor.process(
                            info, settings.get("output_folder"), settings.get("audio_format"))
        finally:
            self.is_downloading = False

