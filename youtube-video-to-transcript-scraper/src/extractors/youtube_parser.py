thonimport logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi

from .utils_text import join_segments, normalize_whitespace

logger = logging.getLogger(__name__)

def _extract_video_id(url: str) -> Optional[str]:
    """
    Extract the video ID from a variety of YouTube URL formats.

    Examples:
        https://www.youtube.com/watch?v=dQw4w9WgXcQ
        https://youtu.be/dQw4w9WgXcQ
        https://www.youtube.com/embed/dQw4w9WgXcQ
    """
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path

        # youtu.be short link
        if "youtu.be" in host:
            video_id = path.lstrip("/")
            return video_id or None

        # Standard watch URL or others with query params
        query = parse_qs(parsed.query)
        if "v" in query and query["v"]:
            return query["v"][0]

        # Embedded or other path-based formats
        parts = path.split("/")
        for idx, value in enumerate(parts):
            if value == "embed" and idx + 1 < len(parts):
                return parts[idx + 1]

        # Fallback: if path looks like /VIDEO_ID
        if len(parts) == 2 and parts[1]:
            return parts[1]

        return None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to parse video ID from URL %s: %s", url, exc)
        return None

@dataclass
class YouTubeTranscriptExtractor:
    language_code: Optional[str] = None

    def _fetch_single_transcript(self, video_id: str) -> Optional[str]:
        """
        Fetch a single transcript as a unified string, or return None if not available.
        """
        languages = [self.language_code] if self.language_code else None
        try:
            segments = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=languages,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to fetch transcript for video_id=%s: %s",
                video_id,
                exc,
            )
            return None

        text = join_segments(segments)
        return normalize_whitespace(text)

    def fetch_transcripts(self, urls: List[str]) -> List[Dict[str, str]]:
        """
        Fetch transcripts for a list of YouTube URLs.

        Returns a list of dicts with:
            {
                "video_id": "...",
                "transcript": "..."
            }
        """
        results: List[Dict[str, str]] = []

        for url in urls:
            video_id = _extract_video_id(url)
            if not video_id:
                logger.warning("Could not extract video ID from URL: %s", url)
                continue

            logger.info("Fetching transcript for video_id=%s", video_id)
            transcript = self._fetch_single_transcript(video_id)
            if transcript is None:
                logger.info(
                    "No transcript available for video_id=%s; skipping.",
                    video_id,
                )
                continue

            results.append(
                {
                    "video_id": video_id,
                    "transcript": transcript,
                }
            )

        return results