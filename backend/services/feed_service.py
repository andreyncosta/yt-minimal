import asyncio
from dataclasses import dataclass

import httpx

from filters import is_allowed, iso8601_to_seconds
from services import auth_service

_YT = "https://www.googleapis.com/youtube/v3"


@dataclass
class FeedItem:
    video_id: str
    title: str
    channel: str
    duration_seconds: int


async def _playlist_video_ids(
    client: httpx.AsyncClient,
    headers: dict,
    playlist_id: str,
    max_items: int = 2,
) -> list[str]:
    resp = await client.get(
        f"{_YT}/playlistItems",
        headers=headers,
        params={"part": "contentDetails", "playlistId": playlist_id, "maxResults": str(max_items)},
    )
    if not resp.is_success:
        return []
    return [
        item["contentDetails"]["videoId"]
        for item in resp.json().get("items", [])
        if item.get("contentDetails", {}).get("videoId")
    ]


async def get_feed(
    user_id: str,
    page_token: str | None = None,
    max_results: int = 20,
) -> tuple[list[FeedItem], str | None]:
    """Fetch the personalised feed for *user_id*.

    Pipeline:
      1. subscriptions.list  → channel IDs (one call)
      2. channels.list       → uploads playlist IDs (one batched call)
      3. playlistItems.list  → recent video IDs (parallel, one call per channel)
      4. videos.list         → titles + durations (one batched call)
      5. filters.is_allowed  → drop Shorts and videos < 3 min
    """
    access_token = await auth_service.get_access_token(user_id)
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        # --- step 1: subscriptions ---
        subs_resp = await client.get(
            f"{_YT}/subscriptions",
            headers=headers,
            params={
                "part": "snippet",
                "mine": "true",
                "maxResults": "10",
                "order": "relevance",
                **({"pageToken": page_token} if page_token else {}),
            },
        )
        subs_resp.raise_for_status()
        subs_data = subs_resp.json()

        channel_ids = [
            item["snippet"]["resourceId"]["channelId"]
            for item in subs_data.get("items", [])
        ]
        if not channel_ids:
            return [], None

        # --- step 2: uploads playlist IDs ---
        ch_resp = await client.get(
            f"{_YT}/channels",
            headers=headers,
            params={"part": "contentDetails", "id": ",".join(channel_ids)},
        )
        ch_resp.raise_for_status()

        playlist_ids = [
            item["contentDetails"]["relatedPlaylists"]["uploads"]
            for item in ch_resp.json().get("items", [])
        ]
        if not playlist_ids:
            return [], subs_data.get("nextPageToken")

        # --- step 3: recent video IDs (parallel, concurrency-capped) ---
        sem = asyncio.Semaphore(15)

        async def _limited(pl_id: str) -> list[str]:
            async with sem:
                return await _playlist_video_ids(client, headers, pl_id)

        nested = await asyncio.gather(*[_limited(pl_id) for pl_id in playlist_ids])
        video_ids: list[str] = [vid for batch in nested for vid in batch]

        if not video_ids:
            return [], subs_data.get("nextPageToken")

        # --- step 4: video details ---
        unique_ids = list(dict.fromkeys(video_ids))[:50]
        vids_resp = await client.get(
            f"{_YT}/videos",
            headers=headers,
            params={"part": "snippet,contentDetails", "id": ",".join(unique_ids)},
        )
        vids_resp.raise_for_status()
        vids_data = vids_resp.json()

    # --- step 5: filter ---
    result: list[FeedItem] = []
    for item in vids_data.get("items", []):
        title: str = item["snippet"]["title"]
        channel: str = item["snippet"]["channelTitle"]
        try:
            duration_seconds = iso8601_to_seconds(item["contentDetails"]["duration"])
        except ValueError:
            continue

        if is_allowed(title, duration_seconds):
            result.append(FeedItem(
                video_id=item["id"],
                title=title,
                channel=channel,
                duration_seconds=duration_seconds,
            ))

    return result[:max_results], subs_data.get("nextPageToken")
