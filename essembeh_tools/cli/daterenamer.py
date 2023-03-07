import json
import shutil
from argparse import ONE_OR_MORE, ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from colorama import Fore, Style

from ..colors import Icons, Label
from ..external import ExternalTool
from ..filesystem import visit
from ..utils import plural

EXIFTOOL = ExternalTool("exiftool", common_args=["-G", "-j"])


EXIF_KEYS_BY_PREFIX = {
    "image/": [
        "Composite:SubSecDateTimeOriginal",
        "Composite:SubSecCreateDate",
        "EXIF:DateTimeOriginal",
        "EXIF:CreateDate",
    ],
    "video/": [
        "QuickTime:CreationDate",
        "QuickTime:CreateDate",
        "QuickTime:MediaCreateDate",
        "QuickTime:CreationDate",
    ],
}


def parse_date(text: str) -> datetime:
    """
    exiftool date are not datetime compatible
    """
    assert len(text) >= 19, f"Invalid date {text}"
    return datetime.fromisoformat(text.replace(":", "-", 2)[0:19])


def get_create_date(file: Path):
    """
    get date prefix
    """
    if not file.exists():
        raise IOError(f"Cannot find {file}")

    with EXIFTOOL.new_command(file) as cmd:
        payload = json.loads(cmd.check_output())

        assert isinstance(payload, list) and len(payload) == 1
        exif = payload[0]

        filetype = exif["File:MIMEType"]
        for prefix, keys in EXIF_KEYS_BY_PREFIX.items():
            if filetype.startswith(prefix):
                for key in keys:
                    if key in exif:
                        return parse_date(exif[key])
                raise ValueError(f"Cannot find date for {file}")

    raise ValueError(f"Unsupported file type {filetype} for {file}")


def get_next_name(folder: Path, prefix: str, suffix: str) -> Path:
    """
    find filename which wouldn't overwrite anything in the given folder
    """
    for index in range(1, 999):
        dest = folder / f"{prefix}{index:03}{suffix}"
        if not dest.exists():
            return dest
    raise ValueError(f"Cannot find a suitable filename in {folder}")


def run():
    """
    entrypoint
    """
    parser = ArgumentParser()
    parser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        help="dry-run mode, do not change anything",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="visit folder content",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="move renamed files in this folder",
    )
    parser.add_argument(
        "files",
        nargs=ONE_OR_MORE,
        type=Path,
        help="files to rename",
    )
    args = parser.parse_args()
    count_already_named, count_error, count_renamed = 0, 0, 0
    with ThreadPoolExecutor() as executor:
        jobs = {
            executor.submit(get_create_date, f): f
            for f in visit(args.files, recursive=args.recursive)
        }
        for job in as_completed(jobs):
            source = jobs[job]
            try:
                create_date = job.result()
                prefix = create_date.strftime("%Y-%m-%d_%Hh%Mm%Ss_")
                if source.name.startswith(prefix) and (
                    args.output is None or source.parent == args.output
                ):
                    count_already_named += 1
                    print(Icons.RED_FLAG, f"{Label.file(source)} is already renamed")
                else:
                    target = get_next_name(
                        args.output or source.parent, prefix, source.suffix.lower()
                    )
                    if args.dryrun:
                        count_renamed += 1
                        print(
                            Icons.DRYRUN,
                            f"{Label.file(source)} would be renamed {Label.file(target)} {Fore.CYAN}(dryrun){Style.RESET_ALL}",
                        )
                    else:
                        shutil.move(source, target)
                        count_renamed += 1
                        print(
                            Icons.OK,
                            f"{Label.file(source)} was renamed {Label.file(target)}",
                        )
            except KeyboardInterrupt:
                executor.shutdown(wait=False, cancel_futures=True)
                exit(1)
            except BaseException as error:  # pylint: disable=broad-except
                count_error += 1
                print(
                    Icons.BOOM,
                    f"cannot be renamed {Label.file(source)}: {Label.error(error)}",
                )

    if count_renamed:
        print(
            "   ",
            Icons.DRYRUN if args.dryrun else Icons.OK,
            f"{count_renamed} {plural('file', count_renamed)} {'would be ' if args.dryrun else ''}renamed",
        )
    if count_already_named:
        print(
            "   ",
            Icons.RED_FLAG,
            f"{count_already_named} {plural('file', count_already_named)} already named",
        )
    if count_error:
        print(
            "   ",
            Icons.BOOM,
            f"{count_error} {plural('error', count_error)}",
        )
