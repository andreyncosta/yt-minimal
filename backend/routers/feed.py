from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict

from dependencies.auth import CurrentUser
from limiter import limiter, user_or_ip_key
from services import feed_service

router = APIRouter(prefix="/feed", tags=["feed"])


class VideoItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_id: str
    title: str
    channel: str
    duration_seconds: int


class FeedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[VideoItem]
    next_page_token: str | None = None


@router.get("/", response_model=FeedResponse)
@limiter.limit("200/minute", key_func=user_or_ip_key)
async def get_feed(
    request: Request,
    user_id: CurrentUser,
    page_token: Annotated[str | None, Query()] = None,
    max_results: Annotated[int, Query(ge=1, le=50)] = 20,
) -> FeedResponse:
    """Return the authenticated user's personalised feed, filtered to videos
    >= 3 minutes and without '#shorts' in the title."""
    try:
        items, next_page_token = await feed_service.get_feed(
            user_id=user_id,
            page_token=page_token,
            max_results=max_results,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="YouTube session expired — please log in again",
            )
        raise HTTPException(status_code=502, detail="YouTube API error")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch feed")

    return FeedResponse(
        items=[
            VideoItem(
                video_id=item.video_id,
                title=item.title,
                channel=item.channel,
                duration_seconds=item.duration_seconds,
            )
            for item in items
        ],
        next_page_token=next_page_token,
    )
