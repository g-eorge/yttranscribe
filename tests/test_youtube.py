from unittest.mock import MagicMock

from yttranscribe.youtube import (
    get_playlist_metadata,
    get_playlist_video_ids,
    get_video_metadata,
)


def _mock_client():
    return MagicMock()


class TestGetVideoMetadata:
    def test_returns_normalized_dict(self):
        client = _mock_client()
        client.videos().list().execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "title": "Test Video",
                        "channelTitle": "Test Channel",
                        "channelId": "UC123",
                        "publishedAt": "2024-03-15T10:00:00Z",
                        "description": "A description",
                        "tags": ["tag1", "tag2"],
                    },
                    "contentDetails": {"duration": "PT12M34S"},
                    "statistics": {"viewCount": "1234567"},
                }
            ]
        }

        result = get_video_metadata(client, "abc123")
        assert result["title"] == "Test Video"
        assert result["channel"] == "Test Channel"
        assert result["channel_id"] == "UC123"
        assert result["published"] == "2024-03-15"
        assert result["duration"] == "PT12M34S"
        assert result["description"] == "A description"
        assert result["views"] == "1,234,567"
        assert result["tags"] == ["tag1", "tag2"]

    def test_missing_video(self):
        client = _mock_client()
        client.videos().list().execute.return_value = {"items": []}

        result = get_video_metadata(client, "missing")
        assert result["title"] == "Unknown (missing)"
        assert result["tags"] == []

    def test_no_tags(self):
        client = _mock_client()
        client.videos().list().execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "title": "No Tags",
                        "channelTitle": "Chan",
                        "channelId": "UC1",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "description": "",
                    },
                    "contentDetails": {"duration": "PT1M"},
                    "statistics": {"viewCount": "0"},
                }
            ]
        }
        result = get_video_metadata(client, "vid1")
        assert result["tags"] == []


class TestGetPlaylistMetadata:
    def test_returns_metadata(self):
        client = _mock_client()
        client.playlists().list().execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "title": "My Playlist",
                        "channelTitle": "My Channel",
                    },
                    "contentDetails": {"itemCount": 10},
                }
            ]
        }

        result = get_playlist_metadata(client, "PL123")
        assert result["playlist_id"] == "PL123"
        assert result["title"] == "My Playlist"
        assert result["channel"] == "My Channel"
        assert result["video_count"] == 10


class TestGetPlaylistVideoIds:
    def test_single_page(self):
        client = _mock_client()
        client.playlistItems().list().execute.return_value = {
            "items": [
                {"contentDetails": {"videoId": "v1"}},
                {"contentDetails": {"videoId": "v2"}},
            ],
        }

        result = get_playlist_video_ids(client, "PL123")
        assert result == ["v1", "v2"]

    def test_multiple_pages(self):
        client = _mock_client()
        page1 = {
            "items": [{"contentDetails": {"videoId": "v1"}}],
            "nextPageToken": "page2token",
        }
        page2 = {
            "items": [{"contentDetails": {"videoId": "v2"}}],
        }
        client.playlistItems().list().execute.side_effect = [page1, page2]

        result = get_playlist_video_ids(client, "PL123")
        assert result == ["v1", "v2"]

    def test_empty_playlist(self):
        client = _mock_client()
        client.playlistItems().list().execute.return_value = {"items": []}

        result = get_playlist_video_ids(client, "PL123")
        assert result == []
