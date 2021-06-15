"""repo-stream command line interface"""

import argparse
import sys

from repo_stream import __version__
from repo_stream.update import update


DESCRIPTION = (
    "Run all configured repo-stream hooks for a set of Github users/organizations."
)


def build_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version number and exit.",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help=(
            "Don't open pull requests, just writes actions that would make to"
            " stderr."
        ),
    )
    parser.add_argument(
        "--hook",
        action="store_true",
        dest="hook",
        help=("Run the repo-stream hook itself. Just exit with code 0 doing nothing."),
    )
    parser.add_argument(
        "-i",
        "--include-forks",
        action="store_true",
        dest="include_forks",
        help="Include forked repositories getting all repositories from users.",
    )
    parser.add_argument("usernames", nargs="*")
    parser.add_argument("-config", "--config", dest="ignoreme_config", default=None)
    parser.add_argument("-updater", "--updater", dest="ignoreme_updater", default=None)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.hook:
            exitcode = 0
            if not args.ignoreme_config:
                sys.stderr.write(
                    "You must define a repository for your configuration file"
                    " using the argument '-config/--config'.\n"
                )
                exitcode = 1
            if not args.ignoreme_updater:
                sys.stderr.write(
                    "You must define a configuration file for your updater"
                    " using the argument '-updater/--updater'.\n"
                )
                exitcode = 1
        else:
            exitcode = update(
                args.usernames,
                include_forks=args.include_forks,
                dry_run=args.dry_run,
            )
    except Exception:
        raise
    else:
        return exitcode


if __name__ == "__main__":
    sys.exit(main())
