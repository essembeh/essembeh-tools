import mimetypes
from argparse import _ActionsContainer
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple, Union

import magic

mimetypes.init()


@contextmanager
def parser_group(
    parser: _ActionsContainer, name: str = "options group", exclusive: bool = False
) -> Generator[_ActionsContainer, None, None]:
    if exclusive:
        yield parser.add_mutually_exclusive_group()
    else:
        yield parser.add_argument_group(name)


def guess_extension(file: Path) -> Optional[str]:
    if (mime := get_mime(file)) is not None:
        return mimetypes.guess_extension(mime, strict=False)


def get_mime(file: Path) -> str | None:
    return magic.from_file(file, mime=True)


def plural(
    sing: str,
    count: int = 0,
    plur: Optional[str] = None,
    suffix: str = "s",
    items: Union[List, Tuple, Dict, None] = None,
):
    if plur is None:
        plur = sing + suffix
    if items is not None:
        count = len(items)
    return plur if count > 1 else sing


def sizeof_fmt(num: float, suffix="B"):
    """
    simply display a human readable size
    """
    for unit in ("", "K", "M", "G"):
        if abs(num) < 1024:
            return f"{num:0.1f} {unit}{suffix}"
        num /= 1024.0
    raise ValueError()
