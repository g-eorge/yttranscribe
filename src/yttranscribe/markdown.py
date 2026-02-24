import re
from datetime import date

from yttranscribe.transcript import format_timestamp


def _yaml_escape(value: str) -> str:
    """Escape a string for safe inclusion in YAML front matter."""
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def slugify(title: str) -> str:
    """Convert a title to a filename-safe slug."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug


def _format_duration(iso_duration: str) -> str:
    """Convert ISO 8601 duration (PT12M34S) to human-readable (12:34)."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not m:
        return iso_duration
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    seconds = int(m.group(3) or 0)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _anchor(title: str) -> str:
    """Generate a GitHub-style markdown anchor from a heading."""
    anchor = title.lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    return anchor


def _render_transcript_blocks(blocks: list[dict], video_id: str) -> str:
    """Render transcript blocks with timestamp links."""
    lines = []
    for block in blocks:
        start_sec = int(block["start"])
        ts = format_timestamp(block["start"])
        url = f"https://www.youtube.com/watch?v={video_id}&t={start_sec}s"
        lines.append(f"[{ts}]({url})")
        lines.append(block["text"])
        lines.append("")
    return "\n".join(lines)


def render_video_section(
    metadata: dict,
    transcript_blocks: list[dict] | None,
    video_id: str,
    heading_level: int = 2,
) -> str:
    """Render a single video section (metadata + description + transcript)."""
    h = "#" * heading_level
    sub_h = "#" * (heading_level + 1)
    title = metadata["title"]
    channel = metadata["channel"]
    published = metadata["published"]
    duration = _format_duration(metadata["duration"])
    url = f"https://www.youtube.com/watch?v={video_id}"

    parts = [f"{h} {title}", ""]

    # Metadata table
    parts.append(f"{sub_h} Metadata")
    parts.append("")
    parts.append("| Field | Value |")
    parts.append("|-------|-------|")
    parts.append(f"| Video ID | {video_id} |")
    parts.append(f"| Channel | {channel} |")
    parts.append(f"| Published | {published} |")
    parts.append(f"| Duration | {duration} |")

    if "views" in metadata:
        parts.append(f"| Views | {metadata['views']} |")
    if metadata.get("tags"):
        parts.append(f"| Tags | {', '.join(metadata['tags'])} |")

    parts.append(f"| URL | {url} |")
    parts.append("")

    # Description
    if metadata.get("description"):
        parts.append(f"{sub_h} Description")
        parts.append("")
        parts.append(metadata["description"])
        parts.append("")

    # Transcript
    parts.append(f"{sub_h} Transcript")
    parts.append("")
    if transcript_blocks:
        parts.append(_render_transcript_blocks(transcript_blocks, video_id))
    else:
        parts.append("*No transcript available for this video.*")
        parts.append("")

    return "\n".join(parts)


def render_video_info(metadata: dict, video_id: str) -> str:
    """Render metadata-only markdown for a video (no transcript)."""
    title = metadata["title"]
    channel = metadata["channel"]
    published = metadata["published"]
    duration = _format_duration(metadata["duration"])
    url = f"https://www.youtube.com/watch?v={video_id}"

    parts = [f"# {title}", "", "## Metadata", ""]
    parts.append("| Field | Value |")
    parts.append("|-------|-------|")
    parts.append(f"| Video ID | {video_id} |")
    parts.append(f"| Channel | {channel} |")
    parts.append(f"| Published | {published} |")
    parts.append(f"| Duration | {duration} |")

    if "views" in metadata:
        parts.append(f"| Views | {metadata['views']} |")
    if metadata.get("tags"):
        parts.append(f"| Tags | {', '.join(metadata['tags'])} |")

    parts.append(f"| URL | {url} |")
    parts.append("")

    if metadata.get("description"):
        parts.append("## Description")
        parts.append("")
        parts.append(metadata["description"])
        parts.append("")

    return "\n".join(parts)


def render_playlist_info(metadata: dict, video_ids: list[str]) -> str:
    """Render playlist overview markdown with video ID table."""
    title = metadata["title"]
    playlist_id = metadata["playlist_id"]
    channel = metadata.get("channel", "")
    video_count = metadata.get("video_count", len(video_ids))
    url = f"https://www.youtube.com/playlist?list={playlist_id}"

    parts = [f"# {title}", ""]
    parts.append("| Field | Value |")
    parts.append("|-------|-------|")
    parts.append(f"| Playlist ID | {playlist_id} |")
    parts.append(f"| Channel | {channel} |")
    parts.append(f"| Video count | {video_count} |")
    parts.append(f"| URL | {url} |")
    parts.append("")

    parts.append("## Videos")
    parts.append("")
    parts.append("| # | Video ID |")
    parts.append("|---|----------|")
    for i, vid in enumerate(video_ids, 1):
        parts.append(f"| {i} | {vid} |")
    parts.append("")

    return "\n".join(parts)


def render_single_video_doc(
    metadata: dict, transcript_blocks: list[dict] | None, video_id: str
) -> str:
    """Render full document for a single video."""
    title = metadata["title"]
    channel = metadata["channel"]
    channel_id = metadata.get("channel_id", "")
    published = metadata["published"]
    duration = metadata["duration"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    today = date.today().isoformat()

    front_matter = f"""---
type: video
video_id: {video_id}
title: {_yaml_escape(title)}
channel: {_yaml_escape(channel)}
channel_id: {channel_id}
published: {published}
duration: {duration}
url: {url}
fetched: {today}
---"""

    h = "#"
    sub_h = "##"
    parts = [front_matter, "", f"{h} {title}", ""]

    # Metadata table
    parts.append(f"{sub_h} Metadata")
    parts.append("")
    parts.append("| Field | Value |")
    parts.append("|-------|-------|")
    parts.append(f"| Channel | {channel} |")
    parts.append(f"| Published | {published} |")
    parts.append(f"| Duration | {_format_duration(duration)} |")

    if "views" in metadata:
        parts.append(f"| Views | {metadata['views']} |")
    if metadata.get("tags"):
        parts.append(f"| Tags | {', '.join(metadata['tags'])} |")

    parts.append("")

    # Description
    if metadata.get("description"):
        parts.append(f"{sub_h} Description")
        parts.append("")
        parts.append(metadata["description"])
        parts.append("")

    # Transcript
    parts.append(f"{sub_h} Transcript")
    parts.append("")
    if transcript_blocks:
        parts.append(_render_transcript_blocks(transcript_blocks, video_id))
    else:
        parts.append("*No transcript available for this video.*")
        parts.append("")

    return "\n".join(parts)


def render_multi_video_doc(videos: list[dict], playlist_meta: dict | None = None) -> str:
    """Render full document for multiple videos or a playlist.

    Each entry in videos should have: video_id, metadata, transcript_blocks.
    """
    today = date.today().isoformat()

    if playlist_meta:
        playlist_id = playlist_meta["playlist_id"]
        title = playlist_meta["title"]
        channel = playlist_meta.get("channel", "")
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        front_matter = f"""---
type: playlist
playlist_id: {playlist_id}
title: {_yaml_escape(title)}
channel: {_yaml_escape(channel)}
video_count: {len(videos)}
url: {url}
fetched: {today}
---"""
    else:
        title = "Video Transcripts"
        front_matter = f"""---
type: collection
video_count: {len(videos)}
fetched: {today}
---"""

    parts = [front_matter, "", f"# {title}", ""]

    # Table of Contents
    parts.append("## Table of Contents")
    parts.append("")
    for i, video in enumerate(videos, 1):
        vtitle = video["metadata"]["title"]
        vpublished = video["metadata"]["published"]
        anchor = _anchor(vtitle)
        parts.append(f"{i}. [{vtitle}](#{anchor}) — {vpublished}")
    parts.append("")

    # Video sections
    for video in videos:
        parts.append("---")
        parts.append("")
        section = render_video_section(
            metadata=video["metadata"],
            transcript_blocks=video["transcript_blocks"],
            video_id=video["video_id"],
            heading_level=2,
        )
        parts.append(section)

    return "\n".join(parts)
