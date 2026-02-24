from unittest.mock import patch

import pytest

from yttranscribe.mcp_server import (
    get_playlist_info,
    get_playlist_transcripts,
    get_transcript,
    get_video_info,
)

SAMPLE_META = {
    "title": "Test Video",
    "channel": "Test Channel",
    "channel_id": "UC123",
    "published": "2024-03-15",
    "duration": "PT12M34S",
    "description": "A description",
    "views": "1,234,567",
    "tags": ["tag1", "tag2"],
}

SAMPLE_TRANSCRIPT = [
    {"start": 0.0, "text": "hello world", "duration": 5.0},
    {"start": 5.0, "text": "foo bar", "duration": 5.0},
]

SAMPLE_BLOCKS = [{"start": 0.0, "text": "hello world foo bar"}]

SAMPLE_PLAYLIST_META = {
    "playlist_id": "PL123",
    "title": "My Playlist",
    "channel": "My Channel",
    "video_count": 2,
}


class TestGetTranscript:
    @patch("yttranscribe.mcp_server.render_single_video_doc", return_value="# Markdown doc")
    @patch("yttranscribe.mcp_server.group_segments", return_value=SAMPLE_BLOCKS)
    @patch("yttranscribe.mcp_server.fetch_transcript", return_value=SAMPLE_TRANSCRIPT)
    @patch("yttranscribe.mcp_server.get_video_metadata", return_value=SAMPLE_META)
    @patch("yttranscribe.mcp_server.build_youtube_client")
    def test_returns_markdown(self, mock_client, mock_meta, mock_tx, mock_grp, mock_render):
        result = get_transcript("abc123", "en")
        assert result == "# Markdown doc"
        mock_meta.assert_called_once_with(mock_client.return_value, "abc123")
        mock_tx.assert_called_once_with("abc123", "en")
        mock_grp.assert_called_once_with(SAMPLE_TRANSCRIPT)
        mock_render.assert_called_once_with(SAMPLE_META, SAMPLE_BLOCKS, "abc123")

    @patch("yttranscribe.mcp_server.render_single_video_doc", return_value="# No transcript")
    @patch("yttranscribe.mcp_server.fetch_transcript", return_value=None)
    @patch("yttranscribe.mcp_server.get_video_metadata", return_value=SAMPLE_META)
    @patch("yttranscribe.mcp_server.build_youtube_client")
    def test_no_transcript_available(self, mock_client, mock_meta, mock_tx, mock_render):
        result = get_transcript("abc123")
        assert result == "# No transcript"
        mock_render.assert_called_once_with(SAMPLE_META, None, "abc123")

    @patch("yttranscribe.mcp_server.build_youtube_client", side_effect=ValueError("no key"))
    def test_missing_api_key_raises(self, mock_client):
        with pytest.raises(ValueError, match="no key"):
            get_transcript("abc123")


class TestGetVideoInfo:
    @patch("yttranscribe.mcp_server.render_video_info", return_value="# Test Video\n")
    @patch("yttranscribe.mcp_server.get_video_metadata", return_value=SAMPLE_META)
    @patch("yttranscribe.mcp_server.build_youtube_client")
    def test_returns_markdown(self, mock_client, mock_meta, mock_render):
        result = get_video_info("abc123")
        assert result == "# Test Video\n"
        mock_meta.assert_called_once_with(mock_client.return_value, "abc123")
        mock_render.assert_called_once_with(SAMPLE_META, "abc123")

    @patch("yttranscribe.mcp_server.build_youtube_client", side_effect=ValueError("no key"))
    def test_missing_api_key_raises(self, mock_client):
        with pytest.raises(ValueError, match="no key"):
            get_video_info("abc123")


class TestGetPlaylistInfo:
    @patch("yttranscribe.mcp_server.get_playlist_video_ids", return_value=["v1", "v2", "v3"])
    @patch("yttranscribe.mcp_server.get_playlist_metadata", return_value=SAMPLE_PLAYLIST_META)
    @patch("yttranscribe.mcp_server.build_youtube_client")
    def test_returns_markdown(self, mock_client, mock_pl_meta, mock_pl_ids):
        result = get_playlist_info("PL123")
        assert "# My Playlist" in result
        assert "| 1 | v1 |" in result
        assert "| 2 | v2 |" in result
        assert "| 3 | v3 |" in result
        mock_pl_meta.assert_called_once_with(mock_client.return_value, "PL123")
        mock_pl_ids.assert_called_once_with(mock_client.return_value, "PL123")

    @patch("yttranscribe.mcp_server.build_youtube_client", side_effect=ValueError("no key"))
    def test_missing_api_key_raises(self, mock_client):
        with pytest.raises(ValueError, match="no key"):
            get_playlist_info("PL123")

    @patch(
        "yttranscribe.mcp_server.get_playlist_metadata",
        side_effect=ValueError("Playlist XYZ not found."),
    )
    @patch("yttranscribe.mcp_server.build_youtube_client")
    def test_playlist_not_found_raises(self, mock_client, mock_pl_meta):
        with pytest.raises(ValueError, match="not found"):
            get_playlist_info("XYZ")


SAMPLE_META_V1 = {**SAMPLE_META, "title": "Video One", "published": "2024-03-10"}
SAMPLE_META_V2 = {**SAMPLE_META, "title": "Video Two", "published": "2024-03-20"}


class TestGetPlaylistTranscripts:
    @patch("yttranscribe.mcp_server.render_multi_video_doc", return_value="# My Playlist\n## Video One\n## Video Two")
    @patch("yttranscribe.mcp_server.group_segments", return_value=SAMPLE_BLOCKS)
    @patch("yttranscribe.mcp_server.fetch_transcript", return_value=SAMPLE_TRANSCRIPT)
    @patch("yttranscribe.mcp_server.get_video_metadata", side_effect=[SAMPLE_META_V1, SAMPLE_META_V2])
    @patch("yttranscribe.mcp_server.get_playlist_video_ids", return_value=["v1", "v2"])
    @patch("yttranscribe.mcp_server.get_playlist_metadata", return_value=SAMPLE_PLAYLIST_META)
    @patch("yttranscribe.mcp_server.build_youtube_client")
    def test_returns_markdown(self, mock_client, mock_pl_meta, mock_pl_ids, mock_vid_meta, mock_tx, mock_grp, mock_render):
        result = get_playlist_transcripts("PL123")
        assert "My Playlist" in result
        assert "Video One" in result
        assert "Video Two" in result
        mock_pl_meta.assert_called_once_with(mock_client.return_value, "PL123")
        mock_pl_ids.assert_called_once_with(mock_client.return_value, "PL123")
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        assert len(args[0]) == 2
        assert kwargs["playlist_meta"] == SAMPLE_PLAYLIST_META

    @patch("yttranscribe.mcp_server.render_multi_video_doc", return_value="# My Playlist\n## Video Two")
    @patch("yttranscribe.mcp_server.group_segments", return_value=SAMPLE_BLOCKS)
    @patch("yttranscribe.mcp_server.fetch_transcript", return_value=SAMPLE_TRANSCRIPT)
    @patch("yttranscribe.mcp_server.get_video_metadata", side_effect=[Exception("not found"), SAMPLE_META_V2])
    @patch("yttranscribe.mcp_server.get_playlist_video_ids", return_value=["v1", "v2"])
    @patch("yttranscribe.mcp_server.get_playlist_metadata", return_value=SAMPLE_PLAYLIST_META)
    @patch("yttranscribe.mcp_server.build_youtube_client")
    def test_skips_failed_videos(self, mock_client, mock_pl_meta, mock_pl_ids, mock_vid_meta, mock_tx, mock_grp, mock_render):
        result = get_playlist_transcripts("PL123")
        assert "Video Two" in result
        mock_render.assert_called_once()
        args, _ = mock_render.call_args
        assert len(args[0]) == 1
        assert args[0][0]["video_id"] == "v2"

    @patch("yttranscribe.mcp_server.build_youtube_client", side_effect=ValueError("no key"))
    def test_missing_api_key_raises(self, mock_client):
        with pytest.raises(ValueError, match="no key"):
            get_playlist_transcripts("PL123")

    @patch(
        "yttranscribe.mcp_server.get_playlist_metadata",
        side_effect=ValueError("Playlist XYZ not found."),
    )
    @patch("yttranscribe.mcp_server.build_youtube_client")
    def test_playlist_not_found_raises(self, mock_client, mock_pl_meta):
        with pytest.raises(ValueError, match="not found"):
            get_playlist_transcripts("XYZ")
