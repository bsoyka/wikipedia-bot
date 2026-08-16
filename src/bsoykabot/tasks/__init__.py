"""Tasks for BsoykaBot."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bsoykabot import __version__

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pywikibot


@dataclass(frozen=True, slots=True)
class Discovered:
    """A page found by a task's discovery phase.

    Attributes:
        title: The title of the page that may need editing.
        cursor: An opaque token that resumes discovery immediately after
            this page, or None if this task's discovery isn't resumable.
    """

    title: str
    cursor: str | None = None


class Task(ABC):
    """Base class for all tasks.

    A task has a *discovery* phase, which yields the titles of pages that
    may need editing, and a *handling* phase, which computes new text for a
    single page. Neither phase saves pages -- see
    :mod:`bsoykabot.wiki.editor`. In production the two phases run in
    different Lambda functions with an SQS queue between them; locally,
    :mod:`bsoykabot.runner` runs them in the same process.
    """

    name: str
    number: int
    edit_summary_text: str

    @abstractmethod
    def discover(self, cursor: str | None = None) -> Iterator[Discovered]:
        """Yield pages that may need editing.

        Args:
            cursor: A token from a previous partial run, or None to start
                from the beginning.

        Yields:
            Each page that may need editing.
        """

    @abstractmethod
    def handle(self, page: pywikibot.Page) -> str | None:
        """Compute replacement text for a single page.

        Args:
            page: The page to inspect.

        Returns:
            The new page text, or None if the page needs no edit.
        """

    def make_edit_summary(self, edits: str) -> str:
        """Generate a standardized summary for edits made by the task.

        This allows a standard format, including a link to task information,
        the bot version, and a link for reporting errors.

        Args:
            edits: A short description of the edits made by the task.

        Returns:
            A formatted edit summary string.
        """
        return (
            f'{edits} '
            f'([[User:BsoykaBot/Task {self.number}|Task {self.number}]], '
            f'v{__version__}, '
            '[[User talk:BsoykaBot|report errors]])'
        )
