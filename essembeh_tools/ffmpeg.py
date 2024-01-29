"""
Video related utility functions
"""
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from re import fullmatch
from typing import List

import ffmpeg
from jsonpath_ng.ext import parse
from lazy_object_proxy import Proxy

_POSITION_PATTERN = (
    r"(?P<minus>-)?"
    + r"((((?P<hours>[0-9]{1,2}):)?(?P<minutes>[0-6]?[0-9]):)?(?P<seconds>[0-6]?[0-9](\.[0-9]{1,3})?)"
    + r"|(?P<seconds_only>[0-9]+(\.[0-9]{1,3})?)"
    + r"|(?P<percent>(100|[0-9]{1,2}))%)"
)


@dataclass
class Position:
    expression: str

    def get_seconds(self, duration: float) -> float:
        matcher = fullmatch(_POSITION_PATTERN, self.expression)
        assert matcher is not None, f"Cannot parse {self.expression}"

        if matcher.group("percent") is not None:
            out = duration * int(matcher.group("percent")) / 100
        elif matcher.group("seconds_only") is not None:
            out = float(matcher.group("seconds_only"))
        else:
            out = float(matcher.group("seconds"))
            if matcher.group("minutes"):
                out += int(matcher.group("minutes")) * 60
                if matcher.group("hours"):
                    out += int(matcher.group("hours")) * 3600
        if matcher.group("minus") is not None:
            out = duration - out
        assert 0 <= out <= duration, f"Invalid position {self.expression}"
        return out

    def as_string(self, duration: float) -> str:
        return str(timedelta(seconds=self.get_seconds(duration)))

    def __str__(self):
        return self.expression


def get_video_resolution(video: Path) -> tuple[int, int] | None:
    """
    use ffprobe to get the video resolution as tuple
    """
    data = ffmpeg.probe(video)
    for match in parse("$.streams[?codec_type = 'video']").find(data):
        return (int(match.value["width"]), int(match.value["height"]))


def get_video_fps(video: Path) -> float | None:
    """
    use ffprobe to get the video fps
    """
    data = ffmpeg.probe(video)
    for match in parse("$.streams[?codec_type = 'video'].r_frame_rate").find(data):
        value = match.value
        if value.isnumeric():
            return float(value)
        elif (rematch := fullmatch(r"(\d+)/(\d+)", value)) is not None:
            return float(rematch.group(1)) / float(rematch.group(2))


def get_video_duration(video: Path) -> float | None:
    """
    use ffprobe to get the video duration as float
    """
    data = ffmpeg.probe(video)
    for match in parse("$.streams[?codec_type = 'video'].duration").find(data):
        return float(match.value)


def extract_frame(
    video: Path, output: Path, position: Position | None, quiet: bool = True
) -> Path:
    """
    Extract a single frame from a video
    """
    duration = Proxy(lambda: get_video_duration(video))
    ffmpeg.input(
        video, ss=position.get_seconds(duration) if position is not None else 0
    ).output(str(output), vframes=1).overwrite_output().run(quiet=quiet)
    assert output.exists()
    return output


def extract_frames(
    video: Path,
    output_folder: Path,
    start: Position | None = None,
    end: Position | None = None,
    fps: float | None = None,
    extension: str = "jpg",
    quiet: bool = True,
) -> List[Path]:
    duration = Proxy(lambda: get_video_duration(video))
    output_folder.mkdir(parents=True, exist_ok=True)
    ffmpeg_kwargs = {}
    if start is not None:
        ffmpeg_kwargs["ss"] = start.get_seconds(duration)
    if end is not None:
        ffmpeg_kwargs["to"] = end.get_seconds(duration)
    stream = ffmpeg.input(video, **ffmpeg_kwargs)
    if fps is not None:
        stream = stream.filter("fps", fps=fps)

    # check no image already exists
    for f in output_folder.iterdir():
        if f.is_file() and fullmatch(r"[0-9]{8}." + extension, f.name) is not None:
            raise FileExistsError(f"File {f} already exists")
    stream.output(f"{output_folder}/%08d.{extension}").overwrite_output().run(
        quiet=quiet
    )
    return sorted(
        [
            f
            for f in output_folder.iterdir()
            if f.is_file() and fullmatch(r"[0-9]{8}." + extension, f.name) is not None
        ]
    )


def create_video(
    frame_folder: Path,
    output_file: Path,
    fps: float = 30,
    extension: str = "jpg",
    filters: List[str] | None = None,
    quiet: bool = True,
) -> Path:
    stream = ffmpeg.input(
        f"{frame_folder}/*.{extension}", pattern_type="glob", framerate=fps
    )
    if filters is not None:
        for current_filter in filters:
            current_filter_args = {}
            if "=" in current_filter:
                current_filter_args = {
                    x[0]: x[1]
                    for x in map(
                        lambda x: x.split("="),
                        filter(
                            lambda x: "=" in x,
                            current_filter[current_filter.index("=") + 1 :].split(":"),
                        ),
                    )
                }
                current_filter = current_filter[0 : current_filter.index("=")]
            print(
                f"Use ffmpeg filter: {current_filter} with arguments",
                ", ".join(map(lambda x: f"{x[0]}={x[1]}", current_filter_args.items())),
            )
            stream = stream.filter(current_filter, **current_filter_args)
    stream.output(str(output_file)).overwrite_output().run(quiet=quiet)
    return output_file
