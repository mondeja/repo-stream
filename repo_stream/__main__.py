"""repo-stream command line interface"""

from repo_stream import __version__
from repo_stream.update import update
from repo_stream.github import install_github_auth

DESCRIPTION = ("Run all configured repo-stream hooks for a set of"
               " Github users/organizations.")


def build_parser():
    parser = argparse.ArgumentParser(
        version=__version__,
        description=DESCRIPTION,
    )
    parser.add_argument("usernames", nargs="*")
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
    
    return parser


def main():
    parser = build_parser()
    
    args = parser.parse_args()
    
    install_github_auth()

    try:
        update(args.usernames, dry_run=args.dry_run)
    except Exception:
        raise
    else:
        return 0

if __name__ == "__main__":
    exit(main())
