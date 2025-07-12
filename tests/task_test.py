"""Test cases for shared task utilities."""

import pytest

from bsoykabot import __version__
from bsoykabot.tasks import Task


def test_run_not_implemented() -> None:
    """Test that the Task class raises NotImplementedError for run method."""
    task = Task()

    with pytest.raises(NotImplementedError):
        task.run()


def test_make_edit_summary() -> None:
    """Test that the Task class generates accurate edit summaries."""
    task = Task()
    task.number = 123

    assert task.make_edit_summary("Fixing links") == (
        f"Fixing links ([[User:BsoykaBot/Task 123|Task 123]], v{__version__}, "
        "[[User talk:BsoykaBot|report errors]])"
    )
