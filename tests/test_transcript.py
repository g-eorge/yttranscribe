from yttranscribe.transcript import format_timestamp, group_segments


class TestFormatTimestamp:
    def test_zero(self):
        assert format_timestamp(0) == "0:00"

    def test_seconds_only(self):
        assert format_timestamp(45) == "0:45"

    def test_one_minute(self):
        assert format_timestamp(60) == "1:00"

    def test_minutes_and_seconds(self):
        assert format_timestamp(90) == "1:30"

    def test_just_under_an_hour(self):
        assert format_timestamp(3599) == "59:59"

    def test_one_hour(self):
        assert format_timestamp(3600) == "1:00:00"

    def test_hours_minutes_seconds(self):
        assert format_timestamp(3661) == "1:01:01"

    def test_float_truncated(self):
        assert format_timestamp(45.7) == "0:45"


class TestGroupSegments:
    def test_empty(self):
        assert group_segments([]) == []

    def test_single_segment(self):
        segments = [{"start": 0.0, "text": "hello", "duration": 2.0}]
        result = group_segments(segments)
        assert len(result) == 1
        assert result[0]["start"] == 0.0
        assert result[0]["text"] == "hello"

    def test_segments_within_one_block(self):
        segments = [
            {"start": 0.0, "text": "hello", "duration": 5.0},
            {"start": 5.0, "text": "world", "duration": 5.0},
            {"start": 10.0, "text": "foo", "duration": 5.0},
        ]
        result = group_segments(segments, interval=30)
        assert len(result) == 1
        assert result[0]["text"] == "hello world foo"
        assert result[0]["start"] == 0.0

    def test_segments_spanning_multiple_blocks(self):
        segments = [
            {"start": 0.0, "text": "first block", "duration": 2.0},
            {"start": 10.0, "text": "still first", "duration": 2.0},
            {"start": 31.0, "text": "second block", "duration": 2.0},
            {"start": 40.0, "text": "still second", "duration": 2.0},
            {"start": 62.0, "text": "third block", "duration": 2.0},
        ]
        result = group_segments(segments, interval=30)
        assert len(result) == 3
        assert result[0]["text"] == "first block still first"
        assert result[0]["start"] == 0.0
        assert result[1]["text"] == "second block still second"
        assert result[1]["start"] == 31.0
        assert result[2]["text"] == "third block"
        assert result[2]["start"] == 62.0

    def test_exact_boundary(self):
        segments = [
            {"start": 0.0, "text": "a", "duration": 1.0},
            {"start": 30.0, "text": "b", "duration": 1.0},
            {"start": 60.0, "text": "c", "duration": 1.0},
        ]
        result = group_segments(segments, interval=30)
        assert len(result) == 3
        assert result[0]["text"] == "a"
        assert result[1]["text"] == "b"
        assert result[2]["text"] == "c"

    def test_whitespace_stripped(self):
        segments = [
            {"start": 0.0, "text": "  hello  ", "duration": 2.0},
            {"start": 5.0, "text": "  world  ", "duration": 2.0},
        ]
        result = group_segments(segments)
        assert result[0]["text"] == "hello world"

    def test_custom_interval(self):
        segments = [
            {"start": 0.0, "text": "a", "duration": 1.0},
            {"start": 5.0, "text": "b", "duration": 1.0},
            {"start": 11.0, "text": "c", "duration": 1.0},
        ]
        result = group_segments(segments, interval=10)
        assert len(result) == 2
        assert result[0]["text"] == "a b"
        assert result[1]["text"] == "c"
