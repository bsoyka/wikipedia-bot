"""Main command-line interface to run tasks."""

import argparse

import sentry_sdk

from bsoykabot import __version__
from bsoykabot.tasks import fix_nfl_draft_case, fix_proxy_urls


def main() -> None:
    """Enter the command-line interface."""
    sentry_sdk.init(
        dsn="https://e8243b175c82050eaa9ea7f2793d352b@o194227.ingest.us.sentry.io/4509610786422784",
        release="wikipedia-bot@" + __version__,
    )

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

    fix_proxy_urls_parser = subparsers.add_parser(
        "fix-proxy-urls",
        help="2: Replace proxy URLs with direct URLs",
    )

    fix_nfl_draft_case_parser = subparsers.add_parser(
        "fix-nfl-draft-case",
        help="3: Fix capitalization in NFL Draft links",
    )
    fix_nfl_draft_case_parser.add_argument(
        "-c",
        "--create-file",
        action="store_true",
        help="Create a file of links to fix",
    )

    args = parser.parse_args()

    if args.subcommand == "fix-nfl-draft-case":
        fix_nfl_draft_case.main(create_file=args.create_file)
    elif args.subcommand == "fix-proxy-urls":
        fix_proxy_urls.main()
    else:
        parser.print_help()
