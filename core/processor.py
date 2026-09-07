import os
import re
from typing import Dict, Any, Tuple
from core.interfaces import IMetadataProcessor
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3


class MusicMetadataProcessor(IMetadataProcessor):
    def _clean_string(self, text: str) -> str:
        """Removes common YouTube suffixes, prefixes, brackets and clutter."""
        if not text:
            return ""

        # Normalize unicode dashes and alternative separators
        t = re.sub(r'[\u2010\u2012\u2013\u2014\u2015\u2212]', '-', text)
        t = re.sub(r'\s*\|\s*', ' - ', t)
        t = re.sub(r'\s*:\s*', ' - ', t)
        t = re.sub(r'\s*•\s*', ' - ', t)
        t = re.sub(r'\s*//\s*', ' - ', t)
        t = re.sub(r'\s*~\s*', ' - ', t)

        # Remove common annoying tags from music videos (case-insensitive)
        patterns = [
            r'\[\s*(?:official|resmi)?\s*(?:music|video|audio|lyric|visualizer|klip|video klip|4k|hd|hq|1080p|remastered|lyrics|sözleri)?\s*(?:video|audio|klip)?\s*\]',
            r'\(\s*(?:official|resmi)?\s*(?:music|video|audio|lyric|visualizer|klip|video klip|4k|hd|hq|1080p|remastered|lyrics|sözleri)?\s*(?:video|audio|klip)?\s*\)',
            r'\[\s*(?:hd|hq|4k|1080p|audio|visualizer)\s*\]',
            r'\(\s*(?:hd|hq|4k|1080p|audio|visualizer)\s*\)',
            r'\|\s*(?:official|resmi).*$',
        ]

        for p in patterns:
            t = re.sub(p, "", t, flags=re.IGNORECASE)

        # Clean multiple spaces, hyphens, and whitespace
        t = re.sub(r"\s+", " ", t).strip()
        t = t.strip("- ")
        return t

    def _sanitize_filename(self, text: str) -> str:
        """Removes illegal characters for safe filenames on all OS."""
        return "".join([c for c in text if c not in '<>:"/\\|?*']).strip()

    def parse_artist_title(self, info: Dict[str, Any]) -> Tuple[str, str]:
        """
        Extracts clean (Artist, Title) tuple from metadata and video info.
        Guarantees format: 'Artist - Song'
        """
        raw_title = info.get("title", "")
        track = info.get("track")
        artist = info.get("artist")
        uploader = info.get("uploader", "")
        channel = info.get("channel", "")

        cleaned_title = self._clean_string(raw_title)

        # 1. Ideal scenario: Official YouTube Music metadata tags exist
        if artist and track:
            return self._sanitize_filename(artist.strip()), self._sanitize_filename(track.strip())

        # 2. Check if cleaned video title contains " - "
        parts = [p.strip() for p in cleaned_title.split(" - ") if p.strip()]

        # Common record label / publisher names that should be stripped
        known_labels = {
            'netd müzik', 'netd muzik', 'vevo', 'spinnin records', 'wmg',
            'sony music', 'universal music', 'warner music', 'avrupa müzik',
            'poll production', 'dmc', 'grand müzik', 'sems müzik', 'ultra records'
        }

        if len(parts) >= 2:
            if len(parts) == 2:
                final_artist = parts[0]
                final_title = parts[1]
            else:
                # 3 or more parts, e.g. "Label - Artist - Song"
                if parts[0].lower() in known_labels:
                    final_artist = parts[1]
                    final_title = " - ".join(parts[2:])
                else:
                    final_artist = parts[0]
                    final_title = " - ".join(parts[1:])
        else:
            # 3. Fallback when title does not contain " - "
            raw_uploader = artist or channel or uploader or "Bilinmeyen Sanatçı"
            # Strip common suffixes from channel name
            clean_uploader = re.sub(
                r'(VEVO| - Topic|Official|Music|Müzik|Records|Channel)',
                '',
                raw_uploader,
                flags=re.IGNORECASE
            ).strip(' -')

            final_artist = clean_uploader or "Bilinmeyen Sanatçı"
            final_title = cleaned_title

        # Clean duplicate artist in title if present (e.g. "Song" after "Artist - Artist Song")
        if final_title.lower().startswith(final_artist.lower()):
            final_title = final_title[len(final_artist):].strip(' -:')

        final_artist = self._sanitize_filename(final_artist) or "Bilinmeyen Sanatçı"
        final_title = self._sanitize_filename(final_title) or "Bilinmeyen Şarkı"

        return final_artist, final_title

    def _update_id3_tags(self, file_path: str, artist: str, title: str):
        """Updates internal ID3 metadata tags so media players display Artist and Title properly."""
        try:
            try:
                audio = EasyID3(file_path)
            except Exception:
                audio = MP3(file_path)
                audio.add_tags()
                audio = EasyID3(file_path)
            audio['artist'] = artist
            audio['title'] = title
            audio.save()
        except Exception as e:
            print(f"Notice: Could not write ID3 tags for {file_path}: {e}")

    def process(self, info: Dict[str, Any],
                output_folder: str, audio_format: str) -> str:
        """
        Post-download renaming and ID3 tagging.
        Guarantees filename: 'Artist - Song.mp3'
        """
        artist, title = self.parse_artist_title(info)
        new_filename = f"{artist} - {title}"
        target_ext = f".{audio_format}"

        video_id = info.get("id", "")

        # Find the downloaded file in output_folder
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

            # 1. Update ID3 tags first (if audio_format is mp3)
            if audio_format.lower() == "mp3":
                self._update_id3_tags(old_path, artist, title)

            # 2. Rename to 'Artist - Song.mp3'
            if old_path != new_path:
                try:
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    os.rename(old_path, new_path)
                except Exception as e:
                    print(f"Error renaming file to {new_filename}: {e}")

        return new_filename
