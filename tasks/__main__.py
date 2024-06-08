"""Main command-line interface to run tasks."""

import argparse

from . import fix_nfl_draft_case, fix_proxy_urls

parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

fix_proxy_urls_parser = subparsers.add_parser(
    "fix-proxy-urls", help="2: Replace proxy URLs with direct URLs"
)

fix_nfl_draft_case_parser = subparsers.add_parser(
    "fix-nfl-draft-case", help="3: Fix capitalization in NFL Draft links"
)
fix_nfl_draft_case_parser.add_argument(
    "-c", "--create-file", action="store_true", help="Create a file of links to fix"
)

args = parser.parse_args()

if args.subcommand == "fix-nfl-draft-case":
    fix_nfl_draft_case.main(create_file=args.create_file)
elif args.subcommand == "fix-proxy-urls":
    fix_proxy_urls.main()
else:
    parser.print_help()
