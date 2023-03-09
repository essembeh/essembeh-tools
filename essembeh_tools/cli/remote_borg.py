import argparse
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

from ..colors import Color
from ..external import ExternalTool

SSH = ExternalTool("ssh", binary_envvar="SSH_BIN", check_arg="-V")


def run():
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--repodir",
        dest="borg_repo_dir",
        type=Path,
        metavar="DIR",
        help="path to borg repository",
    )
    parser.add_argument(
        "-t",
        "--tty",
        dest="tty",
        action="store_true",
        help="force pseudo-terminal allocation for ssh connection (might be required to accept ssh fingerprints)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        dest="non_interactive",
        action="store_true",
        help="do not ask confirmation before executing command",
    )
    parser.add_argument(
        "--args",
        dest="args_file",
        type=Path,
        metavar="FILE",
        help="use borg arguments from file",
    )
    parser.add_argument(
        "-p",
        "--remote-port",
        dest="remote_port",
        type=int,
        metavar="PORT",
        help="remote server ssh port",
    )
    parser.add_argument(
        "--local-user",
        dest="local_user",
        default=os.getenv("USER"),
        metavar="USER",
        help="local ssh user who can access to the borg repository (default is current user)",
    )
    parser.add_argument(
        "--local-port",
        dest="local_port",
        type=int,
        default=22,
        metavar="PORT",
        help="local ssh port (default is 22)",
    )
    parser.add_argument(
        "--local-host",
        dest="local_host",
        default="localhost",
        metavar="HOST",
        help="local ssh host (default is localhost)",
    )
    parser.add_argument(
        "--tunnel",
        dest="ssh_tunnel",
        type=int,
        default=47022,
        metavar="PORT",
        help="port used to setup the ssh tunnel (you should change it if 47022 is already taken)",
    )

    parser.add_argument("remote_host", metavar="REMOTE_HOST", help="remote ssh host")
    parser.add_argument(
        "borg_args",
        nargs=argparse.REMAINDER,
        metavar="BORG_ARGS",
        help="borg arguments",
    )

    args = parser.parse_args()

    # Some checks
    if args.args_file and len(args.borg_args) > 0:
        print("You cannot provide borg arguments AND --args file", file=sys.stderr)
        sys.exit(1)

    # Build the remote borg repository
    borg_repo_dir = args.borg_repo_dir
    if borg_repo_dir is not None:
        borg_repo_dir = borg_repo_dir.resolve()
    elif "BORG_REPO" in os.environ:
        borg_repo_dir = Path(os.environ["BORG_REPO"]).resolve()
    else:
        print(
            "No BORG_REPO set in environment not given using --repodir/-d",
            file=sys.stderr,
        )
        sys.exit(1)
    borg_repo = (
        f"ssh://{args.local_user}@{args.local_host}:{args.ssh_tunnel}{borg_repo_dir}"
    )

    # Build the command line
    with SSH.new_command() as command:
        # enables forwarding of the authentication agent connection
        command.append("-A")
        # custom port
        command.append_if(args.remote_port, "-p", args.remote_port)
        # force the TTY
        command.append_if(args.tty, "-t")
        # create the tunnel
        command += ["-R", f"{args.ssh_tunnel}:{args.local_host}:{args.local_port}"]

        command.append(args.remote_host)

        # borg command
        command += [f"BORG_REPO={borg_repo}", "borg"]
        if args.args_file:
            command += [
                line
                for line in map(str.strip, args.args_file.readlines().splitlines())
                if len(line) > 0 and not line.startswith("#")
            ]
        else:
            command += args.borg_args

        # execute command
        print("Command:", Color.YELLOW(command))
        if (
            args.non_interactive
            or input("Execute command? (y/N) ").strip().lower() == "y"
        ):
            print("----------------------------------------")
            sys.exit(command.run().returncode)
