import hashlib
import shutil
from argparse import ONE_OR_MORE, ArgumentParser, ArgumentTypeError
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

from ..colors import Color, Icons, Label
from ..filesystem import visit
from ..utils import guess_extension, parser_group, plural


def noslash(text: str):
    if "/" in text:
        print(Color.RED(f"Path delimiter '/' cannot be used in '{text}'"))
        raise ArgumentTypeError()
    return text


def compute_hash(hfunc: Callable, file: Path) -> str:
    algo = hfunc()
    with file.open("rb") as file_fd:
        for chunk in iter(lambda: file_fd.read(4096), b""):
            algo.update(chunk)
    return algo.hexdigest()


def compute_filename(
    fingerprint: str,
    length: int = 0,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    extension: Optional[str] = None,
) -> str:
    assert len(fingerprint) > 0
    assert length >= 0
    return (
        (prefix or "")
        + (fingerprint if length == 0 else fingerprint[0:length])
        + (suffix or "")
        + (extension or "")
    )


def run():
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print more information",
    )
    parser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        help="dry-run mode, do not change anything",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        metavar="THREADS",
        help="parallel jobs",
    )
    with parser_group(parser, exclusive=True) as group:
        for hlabel, hfunc in (
            ("md5", hashlib.md5),
            ("sha1", hashlib.sha1),
            ("sha224", hashlib.sha224),
            ("sha256", hashlib.sha256),
            ("sha384", hashlib.sha384),
            ("sha512", hashlib.sha512),
        ):
            group.add_argument(
                f"--{hlabel}",
                dest="hfunc",
                action="store_const",
                const=hfunc,
                default=hashlib.md5,
                help=f"use {hlabel} to compute file fingerprint",
            )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="visit folder content",
    )
    parser.add_argument(
        "-l",
        "--len",
        dest="length",
        type=int,
        metavar="N",
        default=0,
        help="truncate fingerprint to N chars",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        type=noslash,
        metavar="PREFIX",
        help="prefix filename with PREFIX",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        type=noslash,
        metavar="SUFFIX",
        help="prefix filename with SUFFIX",
    )
    with parser_group(parser, exclusive=True) as group:
        group.add_argument(
            "-e",
            "--ext",
            action="store_true",
            help="append current file extension to target filename",
        )
        group.add_argument(
            "-E", "--auto-ext", action="store_true", help="append automatic extension"
        )
    parser.add_argument(
        "-o",
        "--output",
        dest="folder",
        type=Path,
        help="rename files in specific folder",
    )
    parser.add_argument(
        "files",
        nargs=ONE_OR_MORE,
        type=Path,
        help="files to rename",
    )
    args = parser.parse_args()

    count_already_named, count_error, count_renamed = 0, 0, 0

    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        jobs = {
            executor.submit(compute_hash, args.hfunc, f): f
            for f in visit(args.files, recursive=args.recursive, verbose=args.verbose)
        }
        for job in as_completed(jobs):
            source = jobs[job]
            fingerprint = job.result()
            extension = None
            if args.ext:
                extension = source.suffix
            elif args.auto_ext:
                extension = guess_extension(source)

            newfilename = compute_filename(
                fingerprint,
                length=args.length,
                prefix=args.prefix,
                suffix=args.suffix,
                extension=extension,
            )

            assert len(newfilename) > 0
            target = (args.folder or source.parent) / newfilename

            if source == target:
                count_already_named += 1
                if args.verbose:
                    print(Icons.OK, f"{Label.file(source)} is already renamed")
            elif target.exists():
                count_error += 1
                print(
                    Icons.RED_FLAG,
                    f"{Label.file(source)} cannot be renamed {Label.file(target)}:",
                    Color.RED("destination already exists"),
                )
            elif args.dryrun:
                count_renamed += 1
                print(
                    Icons.DRYRUN,
                    f"{Label.file(source)} would be renamed {Label.file(target)}",
                    Color.CYAN("(dryrun)"),
                )
            else:
                try:
                    if not target.parent.exists():
                        target.parent.mkdir(parents=True)
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
                        f"{Label.file(source)} cannot be renamed {Label.file(target)}:",
                        Label.error(error),
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
            Icons.OK,
            f"{count_already_named} {plural('file', count_already_named)} already named",
        )
    if count_error:
        print(
            "   ",
            Icons.BOOM,
            f"{count_error} {plural('error', count_error)}",
        )
