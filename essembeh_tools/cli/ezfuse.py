"""
ezfuse - Quickly mount fuse filesystems in temporary directories
"""

import argparse
import os
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional

from ..colors import Color, Icons, Label

COMMMANDS = (
    ("q", "umount and exit"),
    ("x", "exit (and keep mountpoint)"),
    ("o", "xdg-open"),
    ("s", "shell"),
    ("m", "mount"),
    ("u", "umount"),
)


def execute(
    *command,
    cwd: Optional[Path] = None,
    check_rc: bool = True,
    extra_env: Optional[Dict[str, Any]] = None,
):
    """
    execute a command using a subprocess
    """
    command = [str(x) for x in command]
    print(Icons.EXEC, "Execute:", Label.command(command))
    env = dict(os.environ)
    if isinstance(extra_env, dict):
        env.update(extra_env)
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=check_rc, env=env)


def run():
    """
    command line entrypoint
    """
    parser = ArgumentParser()
    parser.add_argument(
        "-t",
        "--type",
        action="store",
        help="type of filesystem, which is also the binary to use to mount it",
    )
    parser.add_argument(
        "--force", action="store_true", help="force type without testing binary before"
    )
    parser.add_argument(
        "--pwd",
        action="store_true",
        help="create temporary folder in current directory, default is home folder",
    )
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="arguments to pass to the mount command",
    )
    args = parser.parse_args()

    # Get mount binary
    binary = args.type
    if binary is None:
        prog = Path(sys.argv[0]).name
        if prog == "ezfuse":
            parser.error("missing -t|--type argument")
        if not prog.startswith("ez"):
            raise ValueError(f"Cannot infer fuse type from {prog}")
        binary = prog[2:]
    # Test mount binary
    if not args.force:
        subprocess.check_call(
            [binary, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    # Create mountpoint
    mountpoint = None
    parent_folder = Path.cwd() if args.pwd else Path.home()
    with TemporaryDirectory(
        prefix=f"ezmount-{binary}-", dir=str(parent_folder)
    ) as tempdir:
        mountpoint = Path(tempdir)
    mountpoint.mkdir()
    print(
        Icons.HINT,
        "Using mountpoint",
        Label.folder(mountpoint),
    )
    # Mount
    try:
        execute(binary, *args.extra_args, mountpoint)
    except BaseException as error:  # pylint: disable=broad-except
        print(Label.error(error, message="Error while mounting"))
        # In case of error, try to remove the mountpoint
        print(Icons.HINT, "Remove mountpoint", Label.folder(mountpoint))
        mountpoint.rmdir()
        sys.exit(2)

    mounted = True
    # Question loop
    actions = [a for a, _ in COMMMANDS]
    while True:
        print()
        for cmd, desc in COMMMANDS:
            print(
                Color.DEFAULT(cmd + ":", style="bright"),
                Color.DEFAULT(desc, style="dim"),
            )
        action = None
        while action not in actions:
            try:
                action = input(f"[{'/'.join(actions)}] ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                action = "x"
        print()

        # Mount/Umount
        if action in ("q", "u"):
            if mounted:
                execute("fusermount", "-u", "-z", mountpoint)
                mounted = False
        elif action in ("m", "o", "s"):
            if not mounted:
                execute(binary, *args.extra_args, mountpoint)
                mounted = True

        # Action open/shell
        if action == "o":
            execute("xdg-open", mountpoint)
        elif action == "s":
            # TODO better shell detection and add PS1 prefix
            execute(
                os.getenv("SHELL", "bash"),
                cwd=mountpoint,
                check_rc=False,
                extra_env={"EZMNT": str(mountpoint)},
            )

        # Handle end of loop to quit
        if action in ("x", "q"):
            if not mounted:
                print(Icons.HINT, "Remove mountpoint", Label.folder(mountpoint))
                mountpoint.rmdir()
            else:
                print(Icons.HINT, "Keeping mountpoint", Label.folder(mountpoint))
                print(
                    Icons.HINT,
                    "To umount it run:",
                    Label.command(f"fusermount -u -z {mountpoint}; rmdir {mountpoint}"),
                )
            sys.exit(0)
