from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Request
from pydantic import BaseModel, ConfigDict

from dependencies.auth import CurrentUser
from limiter import limiter, user_or_ip_key
from services.audio_service import AudioExtractionError, VideoUnavailableError
from services import audio_service

router = APIRouter(prefix="/audio", tags=["audio"])

# YouTube video IDs are exactly 11 chars: [A-Za-z0-9_-]
_VIDEO_ID_RE = r"^[A-Za-z0-9_-]{11}$"


class AudioUrlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_id: str
    audio_url: str


@router.get("/{video_id}", response_model=AudioUrlResponse)
@limiter.limit("30/minute", key_func=user_or_ip_key)
async def get_audio_url(
    request: Request,
    video_id: Annotated[str, Path(pattern=_VIDEO_ID_RE)],
    _user_id: CurrentUser,
) -> AudioUrlResponse:
    """Return the direct bestaudio stream URL for a YouTube video.

    The URL is extracted via yt-dlp and returned as-is — this endpoint does
    not proxy audio data. The app is responsible for initiating playback.
    YouTube signed URLs typically expire within a few hours; the app should
    re-call this endpoint rather than caching the URL long-term.
    """
    try:
        audio_url = await audio_service.get_audio_url(video_id)
    except VideoUnavailableError:
        raise HTTPException(status_code=404, detail="Video not found or unavailable")
    except AudioExtractionError:
        raise HTTPException(status_code=502, detail="Failed to extract audio from YouTube")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error")

    return AudioUrlResponse(video_id=video_id, audio_url=audio_url)
