import os
import re
import glob
from typing import Dict, Any
from core.interfaces import IMetadataProcessor


class MusicMetadataProcessor(IMetadataProcessor):
    def _clean_string(self, text: str) -> str:
        """Removes common YouTube suffixes like (Official Video), etc."""
        if not text:
            return ""

        # Remove common annoying tags from music videos
        patterns = [
            r"\[.*?official.*?\]",
            r"\(.*?official.*?\)",
            r"\[.*?lyric.*?\]",
            r"\(.*?lyric.*?\)",
            r"\[.*?audio.*?\]",
            r"\(.*?audio.*?\)",
            r"\[.*?music video.*?\]",
            r"\(.*?music video.*?\)",
            r"\[.*?visualizer.*?\]",
            r"\(.*?visualizer.*?\)",
            r"\[.*?video.*?\]",
            r"\(.*?video.*?\)"
        ]

        cleaned = text
        for p in patterns:
            cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)

        # Clean up multiple spaces, hyphens, etc.
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = cleaned.strip("- ")
        return cleaned

    def _sanitize_filename(self, text: str) -> str:
        # Remove illegal filename characters
        return "".join([c for c in text if c not in '<>:"/\\|?*']).strip()

    def process(self, info: Dict[str, Any],
                output_folder: str, audio_format: str) -> str:
        """Post-download renaming based on metadata."""
        track = info.get("track")
        artist = info.get("artist")
        title = info.get("title", "")
        uploader = info.get("uploader", "")
        channel = info.get("channel", "")
        video_id = info.get("id", "")

        # 1. Determine the best possible Clean Title & Artist
        cleaned_title = self._clean_string(title)

        if track and artist:
            # Ideal scenario: YouTube Music metadata exists
            new_filename = f"{artist} - {track}"
        else:
            # Fallback for standard YouTube videos
            if " - " in cleaned_title:
                # Video title already contains artist and song info
                new_filename = cleaned_title
            else:
                # Extract artist from uploader/channel name, remove "VEVO" or "
                # - Topic"
                best_artist = artist or channel or uploader or "Bilinmeyen Sanatçı"
                best_artist = best_artist.replace("VEVO", "").replace(" - Topic", "").strip()

                if best_artist.lower() in cleaned_title.lower():
                    # If artist name is already in the song title, don't duplicate
                    new_filename = cleaned_title
                else:
                    # Construct "Artist - Title"
                    new_filename = f"{best_artist} - {cleaned_title}"

        # 2. Sanitize to final safety
        new_filename = self._sanitize_filename(new_filename)
        if not new_filename:
            new_filename = "Bilinmeyen Şarkı"

        # 3. Find the downloaded file using video ID (avoiding glob bracket issues with [id])
        target_ext = f".{audio_format}"
        matching_files = []
        if os.path.exists(output_folder):
            for fname in os.listdir(output_folder):
                if fname.endswith(target_ext) and (not video_id or video_id in fname):
                    matching_files.append(os.path.join(output_folder, fname))
                    break
            # Fallback if video_id not in filename
            if not matching_files:
                for fname in os.listdir(output_folder):
                    if fname.endswith(target_ext):
                        matching_files.append(os.path.join(output_folder, fname))
                        break

        if matching_files:
            old_path = matching_files[0]
            new_path = os.path.join(output_folder, f"{new_filename}.{audio_format}")

            if old_path != new_path:
                try:
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    os.rename(old_path, new_path)
                except Exception as e:
                    print(f"Error renaming file to {new_filename}: {e}")

        return new_filename

