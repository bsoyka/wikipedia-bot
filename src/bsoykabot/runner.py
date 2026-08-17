"""Drives a task's discovery and handling phases in a single process.

On AWS, discovery and handling run as separate Lambda functions connected
by SQS (see :mod:`bsoykabot.aws.handlers`). Locally -- and when the task is
run from the CLI -- both phases run here, in-process, so there is exactly
one implementation of each task's logic to keep in sync.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pywikibot
from loguru import logger

from bsoykabot.wiki.editor import save_page
from bsoykabot.wiki.site import get_site

if TYPE_CHECKING:
    from bsoykabot.tasks import Task


def run_locally(task: Task, *, limit: int | None = None, dry_run: bool = False) -> None:
    """Run a task's discovery and handling phases in this process.

    Args:
        task: The task to run.
        limit: The maximum number of pages to edit, or None for no limit.
        dry_run: Whether to block all edits, per Pywikibot's ``simulate``.
    """
    if dry_run:
        pywikibot.config.simulate = True

    site = get_site()
    edited = 0

    for discovered in task.discover():
        page = pywikibot.Page(site, discovered.title)
        text = task.handle(page)

        if text is None:
            continue

        if save_page(page, text, task=task):
            edited += 1
            logger.info(f'Edited {page.title()} ({edited} so far)')

        if limit is not None and edited >= limit:
            logger.info(f'Reached the limit of {limit} edits; stopping')
            break
