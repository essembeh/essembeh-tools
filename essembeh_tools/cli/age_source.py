import os
import shlex
import shutil
import signal
import sys
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory

import pexpect
from shellingham import detect_shell

from ..colors import Color, Icons
from ..external import ExternalTool

AGE = ExternalTool("age", check_arg="--version")
AGE_DEFAULT_KEY = Path.home() / ".age" / "key.txt"
SOURCE_COMMAND = {
    "fish": "source",
    "csh": "source",
    "tcsh": "source",
    "nu": "source",
    "bash": ".",
}


def run():
    parser = ArgumentParser()
    parser.add_argument(
        "-i",
        "--identity",
        type=Path,
        default=AGE_DEFAULT_KEY,
        required=not AGE_DEFAULT_KEY.exists(),
        help="age key file",
    )
    parser.add_argument("env_file", type=Path, help="env files to source")

    args = parser.parse_args()

    with TemporaryDirectory() as tempdir:
        env_file = Path(tempdir) / "age.env"
        with AGE.new_command("-i", args.identity, "-d") as age_decrypt:
            age_decrypt.append(args.env_file)
            print(
                f"{Icons.LOCK_AND_KEY} Decrypt {args.env_file} with {Color.YELLOW(age_decrypt)}"
            )
            env_file.write_text(
                age_decrypt.check_output().decode(encoding="utf8")
                + f'\nPS1="({Icons.UNLOCKED} AGE:{args.env_file.name}) $PS1"\n'
            )

        shell_name, shell_path = detect_shell(os.getpid())
        terminal = shutil.get_terminal_size()
        subshell = pexpect.spawn(
            shell_path, ["-i"], dimensions=(terminal.lines, terminal.columns)
        )

        if shell_name in ["zsh", "nu"]:
            subshell.setecho(False)
            if shell_name == "zsh":
                # Under ZSH the source command should be invoked in zsh's bash emulator
                subshell.sendline(f"emulate bash -c '. {shlex.quote(str(env_file))}'")
        else:
            subshell.sendline(
                f"{SOURCE_COMMAND.get(shell_name, '.')} {shlex.quote(str(env_file))}"
            )

        def resize(*args, **kwargs) -> None:
            terminal = shutil.get_terminal_size()
            subshell.setwinsize(terminal.lines, terminal.columns)

        signal.signal(signal.SIGWINCH, resize)

        # Interact with the new shell.
        subshell.interact(escape_character=None)
        subshell.close()

        sys.exit(subshell.exitstatus)
