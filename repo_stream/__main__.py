"""repo-stream command line interface"""

import argparse
import os
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
        help="Run the repo-stream hook itself. Just exit with code 0 doing nothing.",
    )
    parser.add_argument(
        "-i",
        "--include-forks",
        action="store_true",
        dest="include_forks",
        help="Include forked repositories getting all repositories from users.",
    )
    parser.add_argument(
        "-I",
        "--ignore-repositories",
        dest="ignore_repositories",
        default=None,
        metavar="PATH",
        help=(
            "Path to a text file with full names of repositories to ignore,"
            " separated by new lines."
        ),
    )
    parser.add_argument(
        "--clone-depth",
        dest="clone_depth",
        default=1,
        metavar="N",
        help=(
            "GIT clone depth. Is useful to increase it if you want to access"
            " previous commits in the forked branch.",
        ),
    )
    parser.add_argument(
        "usernames",
        nargs="*",
        help="Github users to scan for repository updates.",
    )
    parser.add_argument("-config", "--config", dest="ignoreme_config", default=None)
    parser.add_argument("-updater", "--updater", dest="ignoreme_updater", default=None)

    return parser


def parse_args():
    parser = build_parser()
    args = parser.parse_args()

    if not args.usernames:
        sys.stderr.write("You must pass at least one username to scan.\n")
        sys.exit(1)

    if args.hook:
        if not args.ignoreme_config:
            sys.stderr.write(
                "You must define a repository for your configuration file"
                " using the argument '-config/--config'.\n"
            )
            sys.exit(1)
        if not args.ignoreme_updater:
            sys.stderr.write(
                "You must define a configuration file for your updater"
                " using the argument '-updater/--updater'.\n"
            )
            sys.exit(1)

    return args


def main():
    args = parse_args()
    exitcode = 0
    try:
        if not args.hook:
            repositories_to_ignore = []
            if args.ignore_repositories:
                if not os.path.isfile(args.ignore_repositories):
                    sys.stderr.write(
                        f"File '{args.ignore_repositories}' defined for"
                        " '--ignore-repositories' option doesn't exists.\n"
                    )
                    sys.exit(1)
                else:
                    with open(args.ignore_repositories) as f:
                        repositories_to_ignore.extend(
                            [line.strip() for line in f.readlines() if line.strip()]
                        )

            exitcode = update(
                args.usernames,
                include_forks=args.include_forks,
                repositories_to_ignore=repositories_to_ignore,
                dry_run=args.dry_run,
                clone_depth=args.clone_depth,
            )
    except Exception:
        raise
    else:
        return exitcode


if __name__ == "__main__":
    sys.exit(main())
