from pathlib import Path
from typing import Iterable

from .colors import Color, Icons, Label


def visit(
    files: Iterable[Path], recursive: bool = False, verbose: bool = False
) -> Iterable[Path]:
    for current in sorted(filter(lambda x: isinstance(x, Path), files)):
        if current.is_file():
            yield current
        elif current.is_dir():
            if recursive:
                yield from visit(current.iterdir(), recursive=recursive)
            else:
                if verbose:
                    print(
                        Icons.HINT,
                        f"{Label.folder(current)} is ignored, use {Color.YELLOW('--recursive')} to process directory",
                    )
        elif verbose:
            print(
                Icons.ERROR,
                f"{Label.file(current)} is ignored, not a file nor a directory",
            )
