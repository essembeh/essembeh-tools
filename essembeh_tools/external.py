import shlex
from collections import UserList
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cached_property
from os import environ
from subprocess import DEVNULL, check_call, check_output, run
from typing import Any, Generator, List, Optional


class ExternalToolCommand(UserList):
    @property
    def command(self) -> List[str]:
        return [str(x) for x in self]

    def __str__(self):
        return shlex.join(self.command)

    def append_if(self, test: Any, *args: Any):
        if test:
            self += args

    def check_call(self, **kwargs):
        return check_call(self.command, **kwargs)

    def check_output(self, **kwargs):
        return check_output(self.command, **kwargs)

    def run(self, check: bool = False, **kwargs):
        return run(self.command, check=check, **kwargs)


@dataclass
class ExternalTool:
    """
    helper to run external tools
    """

    _binary: str
    common_args: List[str] = field(default_factory=list)
    binary_envvar: Optional[str] = None
    check_arg: Optional[str] = None

    @cached_property
    def binary(self):
        """
        find and test that the binary is executable
        """
        out = (
            environ.get(self.binary_envvar, self._binary)
            if self.binary_envvar is not None
            else self._binary
        )
        if self.check_arg is not None:
            check_call([out, self.check_arg], stdout=DEVNULL, stderr=DEVNULL)
        return out

    def command(self, *args) -> ExternalToolCommand:
        out = ExternalToolCommand()
        out.append(self.binary)
        out += self.common_args
        out += args
        return out

    @contextmanager
    def with_command(self, *args) -> Generator[ExternalToolCommand, None, None]:
        yield self.command(*args)
