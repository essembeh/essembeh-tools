from argparse import ArgumentParser
from pathlib import Path
from re import fullmatch

from ..colors import Icons, Label
from ..ffmpeg import create_video


def run():
    parser = ArgumentParser()
    parser.add_argument("-o", "--output", type=Path, help="output folder")
    video_group = parser.add_argument_group("video options")
    video_group.add_argument("--fps", type=float, help="frames per second")
    video_group.add_argument(
        "-f",
        "--filter",
        dest="filters",
        action="append",
        help="use ffmpeg filters (example -f avgblur -f deblock ...)",
    )
    parser.add_argument("folder", type=Path, help="folder containing frames")

    args = parser.parse_args()

    filename = args.folder.name
    if (fps := args.fps) is None:
        if (
            m := fullmatch(
                r"^(?P<name>.+?)(?: \(((?P<fps>\d+(\.\d+)?)fps)\))?$", args.folder.name
            )
        ) is not None and m.group("fps") is not None:
            fps = float(m.group("fps"))
            filename = m.group("name")
            print("Guess fps given folder name: {fps}")
        else:
            fps = 30

    output_file = args.output or (Path.cwd() / f"{filename}.mp4")
    assert not output_file.exists()

    create_video(args.folder, output_file, fps, filters=args.filters)
    print(f"{Icons.OK} Created {Label.file(output_file)}")
