import mimetypes
from argparse import _ActionsContainer
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple, Union

import magic


@contextmanager
def parser_group(
    parser: _ActionsContainer, name: str = "options group", exclusive: bool = False
) -> Generator[_ActionsContainer, None, None]:
    if exclusive:
        yield parser.add_mutually_exclusive_group()
    else:
        yield parser.add_argument_group(name)


def get_mime(file: Path) -> str:
    """
    Return the mime of a file
    """
    if not file.exists():
        raise FileNotFoundError(f"Cannot find file: {file}")
    return magic.from_file(str(file.resolve()), mime=True)


def guess_extension(file: Path) -> Optional[str]:
    return mimetypes.guess_extension(get_mime(file))


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
