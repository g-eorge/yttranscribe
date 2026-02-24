import os
import sys

from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv(".env.secret")


def build_youtube_client():
    """Create a YouTube Data API v3 client using an API key."""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("Error: YOUTUBE_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return build("youtube", "v3", developerKey=api_key)


def get_video_metadata(client, video_id: str) -> dict:
    """Fetch metadata for a single video. Returns a normalized dict."""
    response = (
        client.videos().list(part="snippet,contentDetails,statistics", id=video_id).execute()
    )
    items = response.get("items", [])
    if not items:
        print(f"Warning: Video {video_id} not found or unavailable.", file=sys.stderr)
        return {
            "title": f"Unknown ({video_id})",
            "channel": "",
            "channel_id": "",
            "published": "",
            "duration": "",
            "description": "",
            "views": "",
            "tags": [],
        }

    item = items[0]
    snippet = item["snippet"]
    content = item["contentDetails"]
    stats = item.get("statistics", {})

    view_count = stats.get("viewCount", "0")
    try:
        formatted_views = f"{int(view_count):,}"
    except (ValueError, TypeError):
        formatted_views = view_count

    return {
        "title": snippet.get("title", ""),
        "channel": snippet.get("channelTitle", ""),
        "channel_id": snippet.get("channelId", ""),
        "published": snippet.get("publishedAt", "")[:10],
        "duration": content.get("duration", ""),
        "description": snippet.get("description", ""),
        "views": formatted_views,
        "tags": snippet.get("tags", []),
    }


def get_playlist_metadata(client, playlist_id: str) -> dict:
    """Fetch metadata for a playlist."""
    response = client.playlists().list(part="snippet,contentDetails", id=playlist_id).execute()
    items = response.get("items", [])
    if not items:
        print(f"Error: Playlist {playlist_id} not found.", file=sys.stderr)
        sys.exit(1)

    item = items[0]
    snippet = item["snippet"]
    content = item["contentDetails"]

    return {
        "playlist_id": playlist_id,
        "title": snippet.get("title", ""),
        "channel": snippet.get("channelTitle", ""),
        "video_count": content.get("itemCount", 0),
    }


def get_playlist_video_ids(client, playlist_id: str) -> list[str]:
    """Fetch all video IDs from a playlist, handling pagination."""
    video_ids = []
    page_token = None

    while True:
        response = (
            client.playlistItems()
            .list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token,
            )
            .execute()
        )

        for item in response.get("items", []):
            vid = item["contentDetails"]["videoId"]
            video_ids.append(vid)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return video_ids
