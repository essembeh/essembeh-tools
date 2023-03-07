import signal
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from time import sleep
from typing import Iterable

from ..colors import Color, Icons, Label

DEFAULT_COMMAND = r'xdg-open "{}"'


def on_signal(*args, **kwargs):
    raise TimeoutError()


signal.signal(signal.SIGALRM, on_signal)


def filter_comments(iterable: Iterable[str]) -> Iterable[str]:
    """
    Filter to remove comments and empty lines
    """
    return filter(
        lambda line: isinstance(line, str)
        and len(line) > 0
        and not line.startswith("#"),
        map(str.strip, iterable),
    )


def transition(prefix: str, command: str, interactive: bool, timeout: int):
    """
    Handle a transition between 2 commands, with interactive prompt and/or sleep delay
    """
    if timeout > 0:
        signal.alarm(timeout)
        try:
            input(
                f"{prefix} Press ENTER or wait {timeout} seconds to execute: {Color.YELLOW(command)} "
            )
        except TimeoutError:
            print("")
        finally:
            signal.alarm(0)
    else:
        if interactive:
            input(f"{prefix} Press ENTER to execute: {Color.YELLOW(command)} ")
        else:
            print(f"{prefix} Execute:  {Color.YELLOW(command)}")


def execute(command: str, retry: int, retry_delay: int = 1, verbose: bool = False):
    """
    Execute a shell command with retry in case of error
    """
    process = subprocess.run(command, shell=True, check=False)
    if process.returncode == 0:
        print(Color.GREEN("OK"), Color.YELLOW(command))
        return True
    print(Color.RED("ERROR"), Color.YELLOW(command))
    if retry > 0:
        sleep(retry_delay)
        return execute(command, retry - 1, verbose=verbose)
    return False


def run():
    """
    Entrypoint
    """
    parser = ArgumentParser()
    parser.add_argument(
        "-y",
        "--yes",
        dest="interactive",
        action="store_false",
        help="do not ask confirmation before executing command",
    )
    parser.add_argument(
        "-f",
        "--follow",
        dest="follow",
        action="store_true",
        help="read file line per line (useful when using a fifo as input file)",
    )
    parser.add_argument(
        "-x",
        "--execute",
        dest="command",
        metavar="COMMAND",
        default=DEFAULT_COMMAND,
        help=f"command to execute (default is '{DEFAULT_COMMAND}')",
    )
    parser.add_argument(
        "--done",
        dest="done_file",
        type=Path,
        metavar="FILE",
        help="file containing items already processed",
    )
    parser.add_argument(
        "--sleep",
        dest="delay",
        metavar="SECONDS",
        type=int,
        default=0,
        help="delay between commands",
    )
    parser.add_argument(
        "--skip",
        dest="skip",
        metavar="N",
        type=int,
        default=0,
        help="skip N first elements",
    )
    parser.add_argument(
        "--retry",
        dest="retry",
        metavar="N",
        type=int,
        default=3,
        help="retry N times in case of error (default is 0)",
    )
    parser.add_argument(
        "items", type=Path, metavar="FILE", help="file containing elements to open"
    )
    args = parser.parse_args()

    done_list = []

    if args.done_file is not None and args.done_file.is_file():
        done_list += set(filter_comments(args.done_file.read_text().splitlines()))
        print(f"Load {len(done_list)} items from {Label.file(args.done_file)}")

    try:
        count = 1
        assert args.items.exists(), f"Cannot find file {args.items}"
        with args.items.open() as fp:
            content = (
                filter_comments(fp)
                if args.follow
                else list(filter_comments(fp.readlines()))
            )
            for line in content:
                prefix = (
                    f"[{count}/{len(content)}]"
                    if isinstance(content, list)
                    else f"[{count}]"
                )
                command_shell = args.command.replace(r"{}", line)
                if args.skip > 0:
                    print(prefix, Color.CYAN("SKIP"), command_shell)
                    args.skip -= 1
                elif line in done_list:
                    print(prefix, Color.CYAN("IGNORE"), command_shell)
                else:
                    transition(
                        prefix,
                        command_shell,
                        args.interactive,
                        args.delay if count > 1 else 0,
                    )
                    if execute(command_shell, args.retry, verbose=True):
                        done_list.append(line)
                count += 1
    except KeyboardInterrupt:
        pass
    except BaseException as error:  # pylint: disable=broad-except
        print(Icons.BOOM, Label.error(error))
        sys.exit(2)
    finally:
        if len(done_list) > 0 and args.done_file is not None:
            args.done_file.write_text("\n".join(done_list))
            print(f"Save {len(done_list)} items in {Label.file(args.done_file)}")
