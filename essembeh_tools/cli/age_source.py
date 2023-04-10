import os
import shlex
import shutil
import signal
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pexpect
from shellingham import detect_shell

from ..colors import Color, Icons, Label
from ..external import ExternalTool

AGE = ExternalTool("age", check_arg="--version")
EDITOR = ExternalTool("vim", binary_envvar="EDITOR")

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
        "-e", "--edit", action="store_true", help="edit file with default $EDITOR"
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="do not print first line if it is a comment",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="do not create .bak file when encrypted file is edited",
    )
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
        tmp_file = Path(tempdir) / "age.env"
        if args.edit:
            if args.env_file.exists():
                # decrypt the existing file
                age_decrypt = AGE.command("-d", "-i", args.identity, args.env_file)
                print(
                    Icons.LOCK_AND_KEY,
                    f"Decrypt {Label.file(args.env_file)}: {Label.command(age_decrypt)}",
                )
                clear_text = age_decrypt.check_output().decode(encoding="utf8")
            else:
                # default content if file does not exists
                clear_text = (
                    f"# Age encrypted file created on {datetime.now().isoformat(sep=' ',timespec='seconds')}\n"
                    + "export FOO='bar'\n"
                )
            # write the content to a temp file
            tmp_file.write_text(clear_text)
            # edit it with $EDITOR
            EDITOR.command(tmp_file).check_call()
            # encrypt the temp file
            age_encrypt = AGE.command("-e", "-a", "-i", args.identity, tmp_file)
            print(
                Icons.LOCK_AND_KEY,
                f"Encrypt {Label.file(tmp_file)}: {Label.command(age_encrypt)}",
            )
            encrypted_text = age_encrypt.check_output(encoding="utf8")
            if args.env_file.exists() and not args.force:
                # create a backup if needed
                backup_file = args.env_file.parent / f"{args.env_file.name}.bak"
                args.env_file.rename(backup_file)
                print(Icons.HINT, f"Backup file: {Label.file(backup_file)}")
            args.env_file.write_text(encrypted_text)
        else:
            # decrypt the existing file
            age_decrypt = AGE.command("-d", "-i", args.identity, args.env_file)
            print(
                Icons.LOCK_AND_KEY,
                f"Decrypt {Label.file(args.env_file)}: {Label.command(age_decrypt)}",
            )
            clear_text = age_decrypt.check_output().decode(encoding="utf8")
            # display first line if it is a comment
            if not args.quiet and clear_text.startswith("#"):
                print(Icons.HINT, Color.CYAN(clear_text.splitlines()[0]))
            # write it to a temp file and append the new PS1
            tmp_file.write_text(
                clear_text
                + f'\nPS1="({Icons.UNLOCKED} AGE:{args.env_file.name}) $PS1"\n',
            )
            # spawn a new shell
            shell_name, shell_path = detect_shell(os.getpid())
            terminal = shutil.get_terminal_size()
            subshell = pexpect.spawn(
                shell_path, ["-i"], dimensions=(terminal.lines, terminal.columns)
            )
            if shell_name in ["zsh", "nu"]:
                subshell.setecho(False)
                if shell_name == "zsh":
                    # Under ZSH the source command should be invoked in zsh's bash emulator
                    subshell.sendline(
                        f"emulate bash -c '. {shlex.quote(str(tmp_file))}'"
                    )
            else:
                subshell.sendline(
                    f"{SOURCE_COMMAND.get(shell_name, '.')} {shlex.quote(str(tmp_file))}"
                )

            def resize(*args, **kwargs) -> None:
                terminal = shutil.get_terminal_size()
                subshell.setwinsize(terminal.lines, terminal.columns)

            signal.signal(signal.SIGWINCH, resize)

            # interact with the new shell.
            subshell.interact(escape_character=None)
            subshell.close()
            sys.exit(subshell.exitstatus)
