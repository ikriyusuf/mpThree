import os
import shutil
from typing import Callable, Optional, Dict, Any
import yt_dlp
from core.interfaces import IDownloader, ISettings, IMetadataProcessor


def resolve_ffmpeg_location(explicit_location: Optional[str] = None) -> Optional[str]:
    """
    Resolves the directory or executable path for FFmpeg.
    Priority order:
    1. Explicit location passed via settings (if exists)
    2. Local folders within project root:
       - ffmpeg/bin/
       - ffmpeg/
       - bin/
       - project root
       - any unzipped 'ffmpeg*' subfolder
    3. System PATH (via shutil.which("ffmpeg"))
    """
    if explicit_location and os.path.exists(explicit_location):
        return explicit_location

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    is_windows = os.name == "nt"
    target_names = ["ffmpeg.exe", "ffmpeg"] if is_windows else ["ffmpeg"]

    # Candidate directories to inspect
    candidates = [
        os.path.join(project_root, "ffmpeg", "bin"),
        os.path.join(project_root, "ffmpeg"),
        os.path.join(project_root, "bin"),
        project_root,
    ]

    # Also search for extracted folders like 'ffmpeg-*-build' in project root
    if os.path.exists(project_root):
        for item in os.listdir(project_root):
            if item.lower().startswith("ffmpeg") and os.path.isdir(os.path.join(project_root, item)):
                candidates.append(os.path.join(project_root, item, "bin"))
                candidates.append(os.path.join(project_root, item))

    # Check candidates
    for candidate_dir in candidates:
        if os.path.isdir(candidate_dir):
            for binary_name in target_names:
                binary_path = os.path.join(candidate_dir, binary_name)
                if os.path.isfile(binary_path):
                    return candidate_dir  # Returns directory containing ffmpeg / ffprobe

    # Fallback to system PATH
    if shutil.which("ffmpeg"):
        return None  # yt-dlp automatically locates it in system PATH

    return None


class YtDlpDownloader(IDownloader):
    def __init__(self, processor: Optional[IMetadataProcessor] = None):
        self.processor = processor
        self.is_downloading = False

    def build_ydl_options(self,
                          settings: ISettings,
                          progress_hook: Optional[Callable] = None) -> Dict[str, Any]:
        ffmpeg_loc = resolve_ffmpeg_location(settings.get("ffmpeg_location"))

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
            "no_color": True,
            "socket_timeout": 30,
            "concurrent_fragment_downloads": 4,
            "geo_bypass": True,
            "noplaylist": True,
        }

        return opts

    def download(self, url: str, settings: ISettings,
                 progress_hook: Optional[Callable] = None):
        ffmpeg_loc = resolve_ffmpeg_location(settings.get("ffmpeg_location"))
        if not ffmpeg_loc and not shutil.which("ffmpeg"):
            raise FileNotFoundError(
                "FFmpeg bulunamadı! Lütfen FFmpeg'i indirip proje içerisindeki "
                "'ffmpeg' veya 'bin' klasörüne yerleştirin (örn: ffmpeg/ffmpeg.exe veya bin/ffmpeg.exe)."
            )

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
