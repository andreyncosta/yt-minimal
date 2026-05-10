import asyncio

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

_YT_WATCH = "https://www.youtube.com/watch?v={}"

# Keywords in yt-dlp error messages that indicate the video itself is gone/private
_UNAVAILABLE_HINTS = ("unavailable", "private", "not exist", "removed", "deleted", "blocked")


class VideoUnavailableError(Exception):
    """Video is private, deleted, or geo-blocked."""


class AudioExtractionError(Exception):
    """yt-dlp could not extract an audio stream URL."""


class _NullLogger:
    """Discards all yt-dlp log output — prevents tokens/URLs leaking to stdout."""

    def debug(self, msg: str) -> None: ...   # noqa: E704
    def info(self, msg: str) -> None: ...    # noqa: E704
    def warning(self, msg: str) -> None: ... # noqa: E704
    def error(self, msg: str) -> None: ...   # noqa: E704


_YDL_OPTS: dict = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,       # ignore playlist context if a playlist URL slips through
    "logger": _NullLogger(),
}


def _extract_sync(video_id: str) -> str:
    """Blocking yt-dlp call — always run via run_in_executor to avoid blocking the event loop."""
    try:
        with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
            info: dict = ydl.extract_info(_YT_WATCH.format(video_id), download=False)
    except DownloadError as exc:
        if any(hint in str(exc).lower() for hint in _UNAVAILABLE_HINTS):
            raise VideoUnavailableError() from exc
        raise AudioExtractionError() from exc
    except ExtractorError as exc:
        raise AudioExtractionError() from exc

    # Single-format selection → URL is at the top level
    audio_url: str | None = info.get("url")

    # Multi-format result → URL lives in the first requested_formats entry
    if not audio_url:
        requested: list[dict] = info.get("requested_formats") or []
        if requested:
            audio_url = requested[0].get("url")

    if not audio_url:
        raise AudioExtractionError()

    return audio_url


_EXTRACTION_TIMEOUT_S = 15.0


async def get_audio_url(video_id: str) -> str:
    """Return the direct bestaudio stream URL for *video_id* without downloading."""
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, _extract_sync, video_id),
            timeout=_EXTRACTION_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        raise AudioExtractionError()
