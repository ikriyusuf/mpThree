import yt_dlp
import os
import shutil
from typing import Callable, Optional, Dict, Any
from core.interfaces import IDownloader, ISettings, IMetadataProcessor


def resolve_ffmpeg_location(explicit_location: Optional[str] = None) -> Optional[str]:
    """Resolves ffmpeg path from settings, system PATH, or imageio_ffmpeg."""
    if explicit_location and os.path.exists(explicit_location):
        return explicit_location
    if shutil.which("ffmpeg"):
        return None  # yt-dlp will find it in system PATH automatically
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and os.path.exists(ffmpeg_exe):
            return ffmpeg_exe
    except Exception:
        pass
    return None


def resolve_js_runtimes() -> Dict[str, Any]:
    """Detects available JS runtime (system node/deno or nodejs_wheel package)."""
    if shutil.which("node") or shutil.which("deno"):
        return {}
    try:
        import nodejs_wheel
        node_bin = os.path.join(
            os.path.dirname(nodejs_wheel.__file__),
            "node.exe" if os.name == "nt" else "node"
        )
        if os.path.exists(node_bin):
            return {"node": {"path": node_bin}}
    except Exception:
        pass
    return {}


class YtDlpDownloader(IDownloader):
    def __init__(self, processor: Optional[IMetadataProcessor] = None):
        self.processor = processor
        self.is_downloading = False

    def build_ydl_options(self,
                          settings: ISettings,
                          progress_hook: Optional[Callable] = None) -> Dict[str, Any]:
        ffmpeg_loc = resolve_ffmpeg_location(settings.get("ffmpeg_location"))
        js_runtimes = resolve_js_runtimes()

        opts: Dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(settings.get("output_folder"), "%(title)s - [%(id)s].%(ext)s"),
            "ffmpeg_location": ffmpeg_loc,
            "progress_hooks": [progress_hook] if progress_hook else [],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": settings.get("audio_format", "mp3"),
                    "preferredquality": settings.get("audio_quality", "192"),
                },
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            "writethumbnail": True,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "remote_components": ["ejs:github"],
            "no_color": True,
            "socket_timeout": 30,
            "concurrent_fragment_downloads": 4,
            "geo_bypass": True,
            "noplaylist": True,
        }

        if js_runtimes:
            opts["js_runtimes"] = js_runtimes

        return opts

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


