from essembeh_tools.ffmpeg import (
    get_video_duration,
    get_video_fps,
    get_video_resolution,
)
from essembeh_tools.utils import get_mime


def test_ffprobe(sample_video):
    assert get_video_fps(sample_video) == 30
    assert (
        duration := get_video_duration(sample_video)
    ) is not None and 20 < duration < 30
    assert get_video_resolution(sample_video) == (1080, 1920)
    assert get_mime(sample_video) == "video/mp4"


def test_ffprobe2(sample2_video):
    assert (fps := get_video_fps(sample2_video)) is not None and 29 < fps < 30
    assert (
        duration := get_video_duration(sample2_video)
    ) is not None and 120 < duration < 180
    assert get_video_resolution(sample2_video) == (1920, 1080)
    assert get_mime(sample2_video) == "video/mp4"
