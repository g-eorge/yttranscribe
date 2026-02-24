import argparse
import sys

from yttranscribe.markdown import (
    render_multi_video_doc,
    render_single_video_doc,
    slugify,
)
from yttranscribe.transcript import fetch_transcript, group_segments
from yttranscribe.youtube import (
    build_youtube_client,
    get_playlist_metadata,
    get_playlist_video_ids,
    get_video_metadata,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="yttranscribe",
        description="Fetch YouTube video transcripts and metadata to structured markdown.",
    )
    parser.add_argument(
        "ids",
        nargs="+",
        help="One or more YouTube video IDs, or a single playlist ID (with --playlist)",
    )
    parser.add_argument(
        "--playlist",
        "-p",
        action="store_true",
        help="Treat the ID as a playlist ID (only one ID allowed in this mode)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Output file path (default: auto-generated from title)",
    )
    parser.add_argument(
        "--lang",
        "-l",
        default="en",
        help="Transcript language code (default: en)",
    )
    return parser.parse_args(argv)


def _fetch_video(client, video_id: str, lang: str) -> dict:
    """Fetch metadata and transcript for a single video, returning a combined dict."""
    print(f"Fetching metadata for {video_id}...", file=sys.stderr)
    metadata = get_video_metadata(client, video_id)

    print(f"Fetching transcript for {video_id}...", file=sys.stderr)
    raw_transcript = fetch_transcript(video_id, lang)
    transcript_blocks = group_segments(raw_transcript) if raw_transcript else None

    return {
        "video_id": video_id,
        "metadata": metadata,
        "transcript_blocks": transcript_blocks,
    }


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.playlist and len(args.ids) != 1:
        print("Error: --playlist requires exactly one playlist ID.", file=sys.stderr)
        sys.exit(1)

    client = build_youtube_client()

    if args.playlist:
        _run_playlist(client, args)
    elif len(args.ids) == 1:
        _run_single(client, args)
    else:
        _run_multi(client, args)


def _run_single(client, args: argparse.Namespace) -> None:
    video_id = args.ids[0]
    video = _fetch_video(client, video_id, args.lang)
    doc = render_single_video_doc(video["metadata"], video["transcript_blocks"], video_id)

    output = args.output or f"{slugify(video['metadata']['title'])}.md"
    _write_output(output, doc)


def _run_multi(client, args: argparse.Namespace) -> None:
    videos = []
    for video_id in args.ids:
        video = _fetch_video(client, video_id, args.lang)
        videos.append(video)

    videos.sort(key=lambda v: v["metadata"]["published"])
    doc = render_multi_video_doc(videos)

    first_title = videos[0]["metadata"]["title"]
    output = args.output or f"{slugify(first_title)}.md"
    _write_output(output, doc)


def _run_playlist(client, args: argparse.Namespace) -> None:
    playlist_id = args.ids[0]

    print(f"Fetching playlist metadata for {playlist_id}...", file=sys.stderr)
    playlist_meta = get_playlist_metadata(client, playlist_id)

    print("Fetching video IDs from playlist...", file=sys.stderr)
    video_ids = get_playlist_video_ids(client, playlist_id)
    print(f"Found {len(video_ids)} videos.", file=sys.stderr)

    videos = []
    for video_id in video_ids:
        try:
            video = _fetch_video(client, video_id, args.lang)
            videos.append(video)
        except Exception as e:
            print(f"Warning: Skipping video {video_id}: {e}", file=sys.stderr)

    videos.sort(key=lambda v: v["metadata"]["published"])
    doc = render_multi_video_doc(videos, playlist_meta=playlist_meta)

    output = args.output or f"{slugify(playlist_meta['title'])}.md"
    _write_output(output, doc)


def _write_output(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)
    print(f"Written to {path}", file=sys.stderr)
