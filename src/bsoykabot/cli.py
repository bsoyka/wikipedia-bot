"""Main command-line interface to run tasks."""

import argparse

from bsoykabot.runner import run_locally
from bsoykabot.tasks import Task, draft_case, proxy_urls

TASKS = {
    draft_case.DraftCaseTask(),
    proxy_urls.ProxyUrlsTask(),
}

TASKS_BY_NAME: dict[str, Task] = {task.name: task for task in TASKS}


def main() -> None:
    """Enter the command-line interface."""
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')

    for task in TASKS:
        subparser = subparsers.add_parser(
            task.name,
            help=f'Task {task.number}',
        )
        subparser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of pages to edit before stopping.',
        )
        subparser.add_argument(
            '--dry-run',
            action='store_true',
            help='Compute edits without saving them.',
        )

    args = parser.parse_args()

    if args.subcommand in TASKS_BY_NAME:
        run_locally(
            TASKS_BY_NAME[args.subcommand],
            limit=args.limit,
            dry_run=args.dry_run,
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
