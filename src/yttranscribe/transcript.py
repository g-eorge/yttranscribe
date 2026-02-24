import sys

from youtube_transcript_api import YouTubeTranscriptApi


def fetch_transcript(video_id: str, lang: str = "en") -> list[dict] | None:
    """Fetch transcript for a video, returning list of {start, text, duration} dicts or None."""
    api = YouTubeTranscriptApi()
    try:
        transcript = api.fetch(video_id, languages=[lang])
        return transcript.to_raw_data()
    except Exception as e:
        print(f"Warning: Could not fetch transcript for {video_id}: {e}", file=sys.stderr)
        return None


def format_timestamp(seconds: float) -> str:
    """Convert seconds to H:MM:SS or M:SS string."""
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def group_segments(segments: list[dict], interval: int = 30) -> list[dict]:
    """Merge consecutive transcript segments into ~interval-second blocks."""
    if not segments:
        return []

    blocks = []
    current_start = segments[0]["start"]
    current_texts = []
    block_boundary = current_start + interval

    for seg in segments:
        if seg["start"] >= block_boundary and current_texts:
            blocks.append({"start": current_start, "text": " ".join(current_texts)})
            current_start = seg["start"]
            current_texts = []
            block_boundary = current_start + interval
        current_texts.append(seg["text"].strip())

    if current_texts:
        blocks.append({"start": current_start, "text": " ".join(current_texts)})

    return blocks
