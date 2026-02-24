import logging
import sys

from mcp.server.fastmcp import FastMCP

from yttranscribe.markdown import (
    render_multi_video_doc,
    render_playlist_info,
    render_single_video_doc,
    render_video_info,
)
from yttranscribe.transcript import fetch_transcript, group_segments
from yttranscribe.youtube import (
    build_youtube_client,
    get_playlist_metadata,
    get_playlist_video_ids,
    get_video_metadata,
)

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("yttranscribe.mcp")

mcp = FastMCP("yttranscribe")


@mcp.tool()
def get_transcript(video_id: str, lang: str = "en") -> str:
    """Fetch the full transcript and metadata for a YouTube video.

    Use this when the user asks for a video transcript, wants to read/summarize
    a YouTube video, or provides a YouTube URL or video ID.
    """
    client = build_youtube_client()
    logger.info("Fetching metadata for %s", video_id)
    metadata = get_video_metadata(client, video_id)
    logger.info("Fetching transcript for %s (lang=%s)", video_id, lang)
    raw_transcript = fetch_transcript(video_id, lang)
    transcript_blocks = group_segments(raw_transcript) if raw_transcript else None
    return render_single_video_doc(metadata, transcript_blocks, video_id)


@mcp.tool()
def get_video_info(video_id: str) -> str:
    """Look up metadata for a YouTube video without fetching the transcript.

    Use this when the user wants to know the title, channel, description,
    view count, or tags of a video.
    """
    client = build_youtube_client()
    logger.info("Fetching metadata for %s", video_id)
    metadata = get_video_metadata(client, video_id)
    return render_video_info(metadata, video_id)


@mcp.tool()
def get_playlist_info(playlist_id: str) -> str:
    """Get the list of videos in a YouTube playlist.

    Returns playlist metadata and all video IDs. Use this when the user
    mentions a playlist or wants to browse videos in a collection.
    """
    client = build_youtube_client()
    logger.info("Fetching playlist metadata for %s", playlist_id)
    metadata = get_playlist_metadata(client, playlist_id)
    logger.info("Fetching video IDs for playlist %s", playlist_id)
    video_ids = get_playlist_video_ids(client, playlist_id)
    return render_playlist_info(metadata, video_ids)


@mcp.tool()
def get_playlist_transcripts(playlist_id: str, lang: str = "en") -> str:
    """Fetch transcripts for every video in a YouTube playlist in one call.

    Returns a single Markdown document with metadata and transcripts for all
    videos, sorted by publish date. Videos that fail to fetch are skipped.

    Use this when the user wants to read or summarize an entire playlist.
    """
    client = build_youtube_client()
    logger.info("Fetching playlist metadata for %s", playlist_id)
    playlist_meta = get_playlist_metadata(client, playlist_id)
    logger.info("Fetching video IDs for playlist %s", playlist_id)
    video_ids = get_playlist_video_ids(client, playlist_id)
    logger.info("Found %d videos in playlist %s", len(video_ids), playlist_id)

    videos = []
    for video_id in video_ids:
        try:
            logger.info("Fetching video %s", video_id)
            metadata = get_video_metadata(client, video_id)
            raw_transcript = fetch_transcript(video_id, lang)
            transcript_blocks = group_segments(raw_transcript) if raw_transcript else None
            videos.append({
                "video_id": video_id,
                "metadata": metadata,
                "transcript_blocks": transcript_blocks,
            })
        except Exception:
            logger.warning("Skipping video %s: failed to fetch", video_id)

    videos.sort(key=lambda v: v["metadata"]["published"])
    return render_multi_video_doc(videos, playlist_meta=playlist_meta)


if __name__ == "__main__":
    mcp.run()
