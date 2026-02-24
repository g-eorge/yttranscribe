from unittest.mock import patch

import pytest

from yttranscribe.cli import main, parse_args

SAMPLE_META = {
    "title": "Test",
    "channel": "C",
    "published": "2024-01-01",
    "duration": "PT1M",
    "description": "",
    "views": "0",
    "tags": [],
    "channel_id": "",
}

SAMPLE_TRANSCRIPT = [{"start": 0, "text": "hi", "duration": 1}]
SAMPLE_BLOCKS = [{"start": 0, "text": "hi"}]


class TestParseArgs:
    def test_single_id(self):
        args = parse_args(["abc123"])
        assert args.ids == ["abc123"]
        assert args.playlist is False
        assert args.output is None
        assert args.lang == "en"

    def test_multiple_ids(self):
        args = parse_args(["v1", "v2", "v3"])
        assert args.ids == ["v1", "v2", "v3"]

    def test_playlist_flag(self):
        args = parse_args(["--playlist", "PL123"])
        assert args.playlist is True
        assert args.ids == ["PL123"]

    def test_playlist_short(self):
        args = parse_args(["-p", "PL123"])
        assert args.playlist is True

    def test_output_flag(self):
        args = parse_args(["--output", "out.md", "abc123"])
        assert args.output == "out.md"

    def test_output_short(self):
        args = parse_args(["-o", "out.md", "abc123"])
        assert args.output == "out.md"

    def test_lang_flag(self):
        args = parse_args(["--lang", "de", "abc123"])
        assert args.lang == "de"

    def test_lang_short(self):
        args = parse_args(["-l", "es", "abc123"])
        assert args.lang == "es"

    def test_no_ids_fails(self):
        with pytest.raises(SystemExit):
            parse_args([])


class TestMainDispatch:
    @patch("yttranscribe.cli._write_output")
    @patch("yttranscribe.cli.render_single_video_doc", return_value="# Doc")
    @patch("yttranscribe.cli.group_segments", return_value=SAMPLE_BLOCKS)
    @patch("yttranscribe.cli.fetch_transcript", return_value=SAMPLE_TRANSCRIPT)
    @patch("yttranscribe.cli.get_video_metadata", return_value=SAMPLE_META)
    @patch("yttranscribe.cli.build_youtube_client")
    def test_single_video(
        self, mock_client, mock_meta, mock_tx, mock_grp, mock_render, mock_write
    ):
        main(["abc123"])
        mock_meta.assert_called_once()
        mock_tx.assert_called_once_with("abc123", "en")
        mock_render.assert_called_once()
        mock_write.assert_called_once_with("test.md", "# Doc")

    @patch("yttranscribe.cli._write_output")
    @patch("yttranscribe.cli.render_multi_video_doc", return_value="# Multi")
    @patch("yttranscribe.cli.group_segments", return_value=SAMPLE_BLOCKS)
    @patch("yttranscribe.cli.fetch_transcript", return_value=SAMPLE_TRANSCRIPT)
    @patch("yttranscribe.cli.get_video_metadata")
    @patch("yttranscribe.cli.build_youtube_client")
    def test_multi_video(self, mock_client, mock_meta, mock_tx, mock_grp, mock_render, mock_write):
        meta_first = {**SAMPLE_META, "title": "First", "published": "2024-02-01"}
        meta_second = {**SAMPLE_META, "title": "Second", "published": "2024-01-01"}
        mock_meta.side_effect = [meta_first, meta_second]
        main(["v1", "v2"])
        assert mock_meta.call_count == 2
        mock_render.assert_called_once()
        videos = mock_render.call_args[0][0]
        assert videos[0]["metadata"]["published"] == "2024-01-01"

    @patch("yttranscribe.cli._write_output")
    @patch("yttranscribe.cli.render_multi_video_doc", return_value="# PL")
    @patch("yttranscribe.cli.group_segments", return_value=SAMPLE_BLOCKS)
    @patch("yttranscribe.cli.fetch_transcript", return_value=SAMPLE_TRANSCRIPT)
    @patch("yttranscribe.cli.get_video_metadata", return_value=SAMPLE_META)
    @patch("yttranscribe.cli.get_playlist_video_ids", return_value=["v1", "v2"])
    @patch(
        "yttranscribe.cli.get_playlist_metadata",
        return_value={
            "playlist_id": "PL1",
            "title": "My Playlist",
            "channel": "C",
            "video_count": 2,
        },
    )
    @patch("yttranscribe.cli.build_youtube_client")
    def test_playlist(
        self,
        mock_client,
        mock_pl_meta,
        mock_pl_ids,
        mock_meta,
        mock_tx,
        mock_grp,
        mock_render,
        mock_write,
    ):
        main(["--playlist", "PL1"])
        mock_pl_meta.assert_called_once()
        mock_pl_ids.assert_called_once()
        assert mock_meta.call_count == 2
        mock_render.assert_called_once()
        mock_write.assert_called_once_with("my-playlist.md", "# PL")

    @patch("yttranscribe.cli.build_youtube_client")
    def test_playlist_multiple_ids_error(self, mock_client):
        with pytest.raises(SystemExit):
            main(["--playlist", "PL1", "PL2"])

    @patch("yttranscribe.cli._write_output")
    @patch("yttranscribe.cli.render_single_video_doc", return_value="# Doc")
    @patch("yttranscribe.cli.group_segments", return_value=None)
    @patch("yttranscribe.cli.fetch_transcript", return_value=None)
    @patch("yttranscribe.cli.get_video_metadata", return_value=SAMPLE_META)
    @patch("yttranscribe.cli.build_youtube_client")
    def test_no_transcript_doesnt_crash(
        self, mock_client, mock_meta, mock_tx, mock_grp, mock_render, mock_write
    ):
        main(["abc123"])
        mock_render.assert_called_once()

    @patch("yttranscribe.cli._write_output")
    @patch("yttranscribe.cli.render_single_video_doc", return_value="# Doc")
    @patch("yttranscribe.cli.group_segments", return_value=SAMPLE_BLOCKS)
    @patch("yttranscribe.cli.fetch_transcript", return_value=SAMPLE_TRANSCRIPT)
    @patch("yttranscribe.cli.get_video_metadata", return_value=SAMPLE_META)
    @patch("yttranscribe.cli.build_youtube_client")
    def test_lang_passed_through(
        self, mock_client, mock_meta, mock_tx, mock_grp, mock_render, mock_write
    ):
        main(["--lang", "es", "abc123"])
        mock_tx.assert_called_once_with("abc123", "es")

    @patch("yttranscribe.cli._write_output")
    @patch("yttranscribe.cli.render_single_video_doc", return_value="# Doc")
    @patch("yttranscribe.cli.group_segments", return_value=[])
    @patch("yttranscribe.cli.fetch_transcript", return_value=[])
    @patch("yttranscribe.cli.get_video_metadata", return_value=SAMPLE_META)
    @patch("yttranscribe.cli.build_youtube_client")
    def test_custom_output(
        self, mock_client, mock_meta, mock_tx, mock_grp, mock_render, mock_write
    ):
        main(["-o", "custom.md", "abc123"])
        mock_write.assert_called_once_with("custom.md", "# Doc")
