"""Internal utilities shared between tasks."""

from . import __version__


def create_edit_summary(edits: str, *, task: int) -> str:
    """Create an edit summary."""
    return (
        f"{edits} "
        f"([[User:BsoykaBot/Task {task}|Task {task}]], "
        f"v{__version__}, "
        "[[User talk:BsoykaBot|report errors]])"
    )
