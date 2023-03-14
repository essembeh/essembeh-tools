"""
gnome-extensions-cli
"""

import shlex
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from colorama import Back, Fore, Style


class Icons(Enum):
    """
    UTF8 Icons
    """

    OK = "✅"
    ERROR = "❌"
    WARNING = "🚨"
    RED_FLAG = "🚩"
    BOOM = "💥"
    QUESTION = "❓"
    DRYRUN = "🙈"
    HINT = "💡"
    DOT_BLACK = "⚫"
    DOT_WHITE = "⚪"
    DOT_RED = "🔴"
    DOT_BLUE = "🔵"
    PACKAGE = "📦"
    THUMB_UP = "👍"
    TRASH = "🗑"
    LOCK_AND_KEY = "🔐"
    LOCKED = "🔒"
    UNLOCKED = "🔓"
    FOLDER = "📂"
    SHIELD = "🛡"
    EXEC = "⚡"

    def __str__(self):
        return self.value


class Color(Enum):
    """
    Utility tool to use colorama colors
    """

    DEFAULT = None
    BLACK = Fore.BLACK
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    LIGHTBLACK_EX = Fore.LIGHTBLACK_EX
    LIGHTRED_EX = Fore.LIGHTRED_EX
    LIGHTGREEN_EX = Fore.LIGHTGREEN_EX
    LIGHTYELLOW_EX = Fore.LIGHTYELLOW_EX
    LIGHTBLUE_EX = Fore.LIGHTBLUE_EX
    LIGHTMAGENTA_EX = Fore.LIGHTMAGENTA_EX
    LIGHTCYAN_EX = Fore.LIGHTCYAN_EX
    LIGHTWHITE_EX = Fore.LIGHTWHITE_EX

    @staticmethod
    def format(
        *message: str,
        fore: Optional[str] = None,
        back: Optional[str] = None,
        style: Optional[str] = None,
    ) -> str:
        """
        string formatter with color and style
        """
        pre = ""
        post = ""
        if isinstance(fore, str):
            pre += fore
            post += Fore.RESET
        if isinstance(back, str):
            pre += back
            post += Back.RESET
        if isinstance(style, str):
            pre += style
            post += Style.RESET_ALL
        return pre + " ".join(map(str, filter(None, message))) + post

    def __call__(self, *args, style: Optional[str] = None) -> str:
        style = (
            {"dim": Style.DIM, "bright": Style.BRIGHT}.get(style.lower()) or style
            if style is not None
            else style
        )
        return Color.format(*args, fore=self.value, style=style)


class Label:
    """
    __str__ builder for common types
    """

    @staticmethod
    def folder(path: Path) -> str:
        return Color.BLUE(f"{path}/", style="bright")

    @staticmethod
    def file(path: Path) -> str:
        return Label.folder(path.parent) + Color.MAGENTA(path.name, style="bright")

    @staticmethod
    def error(error: BaseException, message: Optional[str] = None) -> str:
        out = ""
        if message is not None:
            out += Color.RED(message + ": ")
        out += Color.RED(error)
        return out

    @staticmethod
    def command(command: Union[str, List[str]]) -> str:
        if isinstance(command, List):
            return Color.YELLOW(*map(shlex.quote, map(str, command)))
        return Color.YELLOW(command)
