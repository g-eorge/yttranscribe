from unittest.mock import patch

from yttranscribe.markdown import (
    render_multi_video_doc,
    render_single_video_doc,
    render_video_section,
    slugify,
)


class TestSlugify:
    def test_simple(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("Hello! @World#") == "hello-world"

    def test_consecutive_spaces(self):
        assert slugify("Hello    World") == "hello-world"

    def test_consecutive_hyphens(self):
        assert slugify("Hello---World") == "hello-world"

    def test_leading_trailing(self):
        assert slugify("--Hello World--") == "hello-world"

    def test_unicode(self):
        assert slugify("Héllo Wörld") == "héllo-wörld"

    def test_underscores_become_hyphens(self):
        assert slugify("hello_world_test") == "hello-world-test"


SAMPLE_METADATA = {
    "title": "Test Video",
    "channel": "Test Channel",
    "channel_id": "UC123",
    "published": "2024-03-15",
    "duration": "PT12M34S",
    "description": "A test description.",
    "views": "1,234,567",
    "tags": ["tag1", "tag2"],
}

SAMPLE_BLOCKS = [
    {"start": 0.0, "text": "Hello and welcome to this video."},
    {"start": 30.0, "text": "Let me explain the concept."},
]


class TestRenderVideoSection:
    def test_contains_heading(self):
        result = render_video_section(SAMPLE_METADATA, SAMPLE_BLOCKS, "abc123")
        assert "## Test Video" in result

    def test_contains_metadata_table(self):
        result = render_video_section(SAMPLE_METADATA, SAMPLE_BLOCKS, "abc123")
        assert "| Channel | Test Channel |" in result
        assert "| Published | 2024-03-15 |" in result
        assert "| Duration | 12:34 |" in result
        assert "| Views | 1,234,567 |" in result
        assert "| Tags | tag1, tag2 |" in result

    def test_contains_description(self):
        result = render_video_section(SAMPLE_METADATA, SAMPLE_BLOCKS, "abc123")
        assert "A test description." in result

    def test_contains_transcript_timestamps(self):
        result = render_video_section(SAMPLE_METADATA, SAMPLE_BLOCKS, "abc123")
        assert "[0:00](https://www.youtube.com/watch?v=abc123&t=0s)" in result
        assert "[0:30](https://www.youtube.com/watch?v=abc123&t=30s)" in result
        assert "Hello and welcome to this video." in result

    def test_no_transcript(self):
        result = render_video_section(SAMPLE_METADATA, None, "abc123")
        assert "*No transcript available for this video.*" in result

    def test_heading_level(self):
        result = render_video_section(SAMPLE_METADATA, SAMPLE_BLOCKS, "abc123", heading_level=3)
        assert "### Test Video" in result
        assert "#### Metadata" in result

    def test_url_in_metadata(self):
        result = render_video_section(SAMPLE_METADATA, SAMPLE_BLOCKS, "abc123")
        assert "| URL | https://www.youtube.com/watch?v=abc123 |" in result

    def test_no_tags(self):
        meta = {**SAMPLE_METADATA, "tags": []}
        result = render_video_section(meta, SAMPLE_BLOCKS, "abc123")
        assert "Tags" not in result

    def test_no_description(self):
        meta = {**SAMPLE_METADATA, "description": ""}
        result = render_video_section(meta, SAMPLE_BLOCKS, "abc123")
        assert "### Description" not in result


class TestRenderSingleVideoDoc:
    @patch("yttranscribe.markdown.date")
    def test_front_matter(self, mock_date):
        mock_date.today.return_value.isoformat.return_value = "2026-02-21"
        result = render_single_video_doc(SAMPLE_METADATA, SAMPLE_BLOCKS, "abc123")
        assert "type: video" in result
        assert 'title: "Test Video"' in result
        assert "video_id: abc123" in result
        assert "channel: Test Channel" in result
        assert "published: 2024-03-15" in result
        assert "duration: PT12M34S" in result
        assert "fetched: 2026-02-21" in result

    @patch("yttranscribe.markdown.date")
    def test_full_structure(self, mock_date):
        mock_date.today.return_value.isoformat.return_value = "2026-02-21"
        result = render_single_video_doc(SAMPLE_METADATA, SAMPLE_BLOCKS, "abc123")
        assert result.startswith("---\n")
        assert "# Test Video" in result
        assert "## Metadata" in result
        assert "## Description" in result
        assert "## Transcript" in result

    @patch("yttranscribe.markdown.date")
    def test_no_transcript(self, mock_date):
        mock_date.today.return_value.isoformat.return_value = "2026-02-21"
        result = render_single_video_doc(SAMPLE_METADATA, None, "abc123")
        assert "*No transcript available for this video.*" in result


class TestRenderMultiVideoDoc:
    def _make_video(self, video_id, title, published):
        return {
            "video_id": video_id,
            "metadata": {
                "title": title,
                "channel": "Test Channel",
                "channel_id": "UC123",
                "published": published,
                "duration": "PT5M0S",
                "description": f"Desc for {title}",
                "views": "100",
                "tags": [],
            },
            "transcript_blocks": [
                {"start": 0.0, "text": f"Transcript for {title}."},
            ],
        }

    @patch("yttranscribe.markdown.date")
    def test_playlist_front_matter(self, mock_date):
        mock_date.today.return_value.isoformat.return_value = "2026-02-21"
        videos = [
            self._make_video("v1", "First Video", "2024-01-10"),
            self._make_video("v2", "Second Video", "2024-02-20"),
        ]
        playlist_meta = {
            "playlist_id": "PL123",
            "title": "My Playlist",
            "channel": "Test Channel",
        }
        result = render_multi_video_doc(videos, playlist_meta=playlist_meta)
        assert "type: playlist" in result
        assert "playlist_id: PL123" in result
        assert 'title: "My Playlist"' in result
        assert "video_count: 2" in result
        assert "fetched: 2026-02-21" in result

    @patch("yttranscribe.markdown.date")
    def test_collection_front_matter(self, mock_date):
        mock_date.today.return_value.isoformat.return_value = "2026-02-21"
        videos = [
            self._make_video("v1", "First Video", "2024-01-10"),
            self._make_video("v2", "Second Video", "2024-02-20"),
        ]
        result = render_multi_video_doc(videos)
        assert "type: collection" in result
        assert "video_count: 2" in result
        assert "# Video Transcripts" in result

    @patch("yttranscribe.markdown.date")
    def test_toc(self, mock_date):
        mock_date.today.return_value.isoformat.return_value = "2026-02-21"
        videos = [
            self._make_video("v1", "First Video", "2024-01-10"),
            self._make_video("v2", "Second Video", "2024-02-20"),
        ]
        result = render_multi_video_doc(videos)
        assert "## Table of Contents" in result
        assert "1. [First Video](#first-video) — 2024-01-10" in result
        assert "2. [Second Video](#second-video) — 2024-02-20" in result

    @patch("yttranscribe.markdown.date")
    def test_video_sections(self, mock_date):
        mock_date.today.return_value.isoformat.return_value = "2026-02-21"
        videos = [
            self._make_video("v1", "First Video", "2024-01-10"),
            self._make_video("v2", "Second Video", "2024-02-20"),
        ]
        result = render_multi_video_doc(videos)
        assert "## First Video" in result
        assert "## Second Video" in result
        assert "Transcript for First Video." in result
        assert "Transcript for Second Video." in result
        assert "---" in result
