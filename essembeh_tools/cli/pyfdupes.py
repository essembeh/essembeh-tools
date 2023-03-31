"""
command line interface
"""

import subprocess
import sys
from argparse import ZERO_OR_MORE, ArgumentParser
from pathlib import Path
from typing import List, Optional, Tuple

from ..colors import Icons, Label
from ..external import ExternalTool
from ..utils import parser_group

FDUPES = ExternalTool(
    "fdupes", check_arg="--version", common_args=["--recurse", "--noempty"]
)


def is_in_folder(file: Path, folders: Optional[List[Path]]) -> bool:
    """
    Check if a file is contained by any given folder
    """
    return folders is not None and any(map(file.is_relative_to, folders))


def find_duplicates(folders: List[Path], quiet: bool = False) -> List[Tuple[Path]]:
    """
    Use fdupes to find supplicates files, and yield the list of files.
    Yielded files are sorted.
    """
    with FDUPES.with_command() as cmd:
        cmd.append_if(quiet, "--quiet")
        cmd += folders

        print("Looking for duplicates ...")
        stdout = cmd.check_output(
            encoding="utf8", stderr=sys.stderr if not quiet else subprocess.DEVNULL
        )
        out = []
        files = []
        for line in stdout.splitlines():
            if len(line) == 0:
                assert len(files) > 1
                out.append(tuple(sorted(files)))
                files = []
            else:
                file = Path(line)
                assert file.is_file()
                files.append(file)
        assert len(files) == 0
        assert len(stdout) >= len(out), f"Error processing: {stdout}"
        return out


def run():
    """
    entry point
    """
    parser = ArgumentParser(description="find and delete duplicate files")

    with parser_group(parser, exclusive=True) as group:
        group.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="print more information",
        )
        group.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="print less information",
        )
    parser.add_argument(
        "--rm",
        action="store_true",
        help="delete duplicated files with no copy in keep folders",
    )
    parser.add_argument(
        "-1",
        "--keep-first",
        action="store_true",
        help="if multiple copies found in keep folders, keep only first copy",
    )
    parser.add_argument(
        "-k",
        "--keep",
        type=Path,
        metavar="DIR",
        action="append",
        help="folders containing files to keep",
    )
    parser.add_argument(
        "folders",
        type=Path,
        metavar="DIR",
        nargs=ZERO_OR_MORE,
        help="folders to analyze",
    )

    args = parser.parse_args()

    try:
        folders = list(args.folders)
        if args.keep is not None:
            folders += args.keep
        files_to_delete = []
        for duplicates in find_duplicates(folders, quiet=args.quiet):
            keep_files = [f for f in duplicates if is_in_folder(f, args.keep)]
            duplicated_files = [f for f in duplicates if f not in keep_files]
            assert len(keep_files) + len(duplicated_files) == len(duplicates)

            if len(keep_files) == 0:
                if args.verbose:
                    print(Icons.FIRE, "No duplicated file found in keep folders:")
                    for file in duplicated_files:
                        print(f"  {Label.file(file)}")
            elif len(duplicated_files) == 0:
                if len(keep_files) > 1 and args.keep_first:
                    for file in keep_files[1:]:
                        print(
                            Icons.TRASH,
                            f"Delete {Label.file(file)} duplicate of {Label.file(keep_files[0])}",
                        )
                        files_to_delete.append(file)
                elif args.verbose:
                    print(Icons.LOCKED, "All duplicated files are in keep folders:")
                    for file in keep_files:
                        print(f"  {Label.file(file)}")
            else:
                files_to_delete += duplicated_files
                for file in duplicated_files:
                    print(
                        Icons.TRASH,
                        f"Delete {Label.file(file)} duplicate of {Label.file(keep_files[0])}",
                    )

        if len(files_to_delete) > 0 and args.rm:
            print(Icons.TRASH, f"Remove {len(files_to_delete)} files")
            for file in files_to_delete:
                file.unlink()

    except KeyboardInterrupt:
        print(Icons.ERROR, "Process interrupted")
        sys.exit(1)
    except BaseException as error:  # pylint: disable=broad-except
        print(Icons.BOOM, Label.error(error, message="Error"))
        raise error
    sys.exit(0)
