"""Main command-line interface to run tasks."""

import argparse

import sentry_sdk

from bsoykabot import __version__
from bsoykabot.tasks import Task, draft_case, proxy_urls

TASKS = {
    draft_case.DraftCaseTask(),
    draft_case.DraftCaseFileTask(),
    proxy_urls.ProxyUrlsTask(),
}

TASKS_BY_NAME: dict[str, Task] = {task.name: task for task in TASKS}


def main() -> None:
    """Enter the command-line interface."""
    sentry_sdk.init(
        dsn='https://e8243b175c82050eaa9ea7f2793d352b@o194227.ingest.us.sentry.io/4509610786422784',
        release='wikipedia-bot@' + __version__,
    )

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')

    for task in TASKS:
        subparsers.add_parser(
            task.name,
            help=f'Task {task.number}',
        )

    args = parser.parse_args()

    if args.subcommand in TASKS_BY_NAME:
        TASKS_BY_NAME[args.subcommand].run()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
