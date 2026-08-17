"""The bot's single page-save path."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pywikibot
from loguru import logger

if TYPE_CHECKING:
    from bsoykabot.tasks import Task


def save_page(page: pywikibot.Page, text: str, *, task: Task) -> bool:
    """Save new text to a page.

    ``OtherPageSaveError`` covers permanent conditions such as page
    protection, the spam blacklist, and abuse filters, so it is logged and
    swallowed here -- retrying would loop forever. Every other exception
    propagates, so that on AWS an SQS redelivery retries the page instead of
    the failure being silently dropped.

    Args:
        page: The page to save.
        text: The new page text.
        task: The task making the edit, used to build the edit summary.

    Returns:
        Whether the page was saved.
    """
    page.text = text

    try:
        page.save(
            summary=task.make_edit_summary(task.edit_summary_text),
            minor=True,
        )
    except pywikibot.exceptions.OtherPageSaveError as error:
        logger.warning(f'Skipping page {page.title()}: {error}')
        return False

    return True
