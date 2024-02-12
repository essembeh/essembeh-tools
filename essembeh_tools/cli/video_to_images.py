from argparse import ArgumentParser
from pathlib import Path

from PIL import Image
from tqdm import tqdm

from ..colors import Icons, Label
from ..ffmpeg import Position, extract_frames, get_video_fps
from ..images import CropFill, Resize, resolution_parse
from ..utils import get_mime


def run():
    parser = ArgumentParser()
    parser.add_argument("-o", "--output", type=Path, help="output folder")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--resize",
        type=lambda t: Resize(resolution_parse(t)),
        dest="resize",
        metavar="WIDTHxHEIGHT",
        help="resize thumbnails",
    )
    group.add_argument(
        "--crop",
        type=lambda t: CropFill(resolution_parse(t)),
        dest="resize",
        metavar="WIDTHxHEIGHT",
        help="crop thumbnails",
    )
    video_group = parser.add_argument_group("video options")
    video_group.add_argument("--fps", type=float, help="frames per second")
    video_group.add_argument(
        "--start",
        type=Position,
        metavar="POSITION",
        help="start position (examples: 42, 2:12, 3%, -40%)",
    )
    video_group.add_argument(
        "--end",
        type=Position,
        metavar="POSITION",
        help="end position (examples: 42, 2:12, 3%, -40%)",
    )
    parser.add_argument("video", type=Path, help="video to process")

    args = parser.parse_args()
    assert get_mime(args.video).startswith("video/")

    fps = args.fps or get_video_fps(args.video)

    output_folder = args.output or (Path.cwd() / f"{args.video.stem} ({fps:.2f}fps)")
    print(f"Extract frames to {Label.folder(output_folder)} ...")
    frames = extract_frames(args.video, output_folder, args.start, args.end, fps)
    print(f"{Icons.OK} {len(frames)} frames extracted")
    if args.resize is not None:
        print(f"Resize frames: {args.resize}")
        for frame in tqdm(frames, unit="frame"):
            with Image.open(frame) as img:
                args.resize.apply(img).save(frame)
        print(f"{Icons.OK} {len(frames)} frames resized")
