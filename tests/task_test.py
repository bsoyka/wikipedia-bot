"""Test cases for shared task utilities."""

from collections.abc import Iterator

import pytest
import pywikibot

from bsoykabot import __version__
from bsoykabot.tasks import Discovered, Task


class _StubTask(Task):
    """A minimal concrete Task, for exercising shared base-class behavior."""

    name = 'stub'
    number = 123
    edit_summary_text = 'Stub edit'

    def discover(self, cursor: str | None = None) -> Iterator[Discovered]:  # ruff: ignore[no-self-use]
        """Yield nothing; this stub is only used for make_edit_summary.

        Returns:
            An empty iterator.
        """
        del cursor
        return iter(())

    def handle(self, page: pywikibot.Page) -> str | None:  # ruff: ignore[no-self-use]
        """Return no edit; this stub is only used for make_edit_summary."""
        del page
        return None


def test_task_is_abstract() -> None:
    """Test that Task cannot be instantiated directly."""
    with pytest.raises(TypeError):
        Task()  # type: ignore[abstract]


def test_make_edit_summary() -> None:
    """Test that a Task generates accurate edit summaries."""
    task = _StubTask()

    assert task.make_edit_summary('Fixing links') == (
        f'Fixing links ([[User:BsoykaBot/Task 123|Task 123]], v{__version__}, '
        '[[User talk:BsoykaBot|report errors]])'
    )
