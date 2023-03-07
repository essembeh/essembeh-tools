import shutil
from argparse import ONE_OR_MORE, ArgumentParser
from pathlib import Path

from ..colors import Icons, Label
from ..utils import parser_group, plural


def move(source, dest):
    assert source.exists() and not dest.exists()
    shutil.move(source, dest)


def copy(source, dest):
    assert source.exists() and not dest.exists()
    shutil.copy(source, dest)


def link(source, dest):
    assert source.exists() and not dest.exists()
    dest.symlink_to(source.resolve())


def run():
    parser = ArgumentParser()
    parser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        help="dry-run mode, do not change anything",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path.cwd(),
        metavar="DIR",
        help=f"dispatch files in given folder, default is {Path.cwd()}",
    )
    with parser_group(parser, exclusive=True) as group:
        group.add_argument(
            "-m",
            "--move",
            dest="operation",
            action="store_const",
            const=move,
            default=move,
            help="move files",
        )
        group.add_argument(
            "-l",
            "--link",
            dest="operation",
            action="store_const",
            const=link,
            default=move,
            help="do symbolic links instead of moving files",
        )
        group.add_argument(
            "-c",
            "--copy",
            dest="operation",
            action="store_const",
            const=copy,
            help="copy files instead of moving them",
        )
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs=ONE_OR_MORE,
        type=Path,
        help="files to move/copy/link",
    )

    args = parser.parse_args()

    dest_folders = [d for d in args.output.iterdir() if d.is_dir()]
    count_ok, count_nodest, count_error = 0, 0, 0
    for source in filter(Path.is_file, args.files):
        candidate = max(
            [d for d in dest_folders if source.name.startswith(d.name)],
            key=lambda x: len(x.name),
            default=None,
        )
        if candidate is None:
            count_nodest += 1
            print(
                Icons.QUESTION,
                f"no subfolder for {Label.file(source)} in {Label.folder(args.output)}",
            )
        else:
            dest = candidate / source.name
            if dest.exists():
                count_error += 1
                print(
                    Icons.ERROR, f"destination file {Label.file(dest)} already exists"
                )
            elif args.dryrun:
                count_ok += 1
                print(
                    Icons.DRYRUN,
                    f"{args.operation.__name__} {Label.file(source)} to {Label.folder(candidate)} (dryrun)",
                )
            else:
                try:
                    args.operation(source, dest)
                    count_ok += 1
                    print(
                        Icons.OK,
                        f"{args.operation.__name__} {Label.file(source)} to {Label.folder(candidate)}",
                    )
                except KeyboardInterrupt:
                    break
                except BaseException as error:  # pylint: disable=broad-except
                    count_error += 1
                    print(
                        Icons.BOOM,
                        f"cannot {args.operation.__name__} {Label.file(source)} to {Label.folder(candidate)}: {Label.error(error)}",
                    )

    print()
    if count_ok:
        print(
            "   ",
            Icons.DRYRUN if args.dryrun else Icons.OK,
            f"{count_ok} {plural('file', count_ok)} {'would be ' if args.dryrun else ''}processed",
        )
    if count_nodest:
        print(
            "   ",
            Icons.QUESTION,
            f"{count_nodest} {plural('file', count_nodest)} without subfolder",
        )
    if count_error:
        print(
            "   ",
            Icons.ERROR,
            f"{count_error} {plural('file', count_error)} with error",
        )
