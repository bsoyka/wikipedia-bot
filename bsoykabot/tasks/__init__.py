"""Tasks for BsoykaBot."""

from bsoykabot import __version__


class Task:
    """Base class for all tasks."""

    name: str
    number: int

    def __init__(self) -> None:
        """Initialize the task."""

    def run(self) -> None:
        """Run the task."""
        raise NotImplementedError

    def make_edit_summary(self, edits: str) -> str:
        """Generate a standardized summary for edits made by the task.

        This allows a standard format, including a link to task information, the
        bot version, and a link for reporting errors.

        Args:
            edits (str): A short description of the edits made by the task.

        Returns:
            str: A formatted edit summary string.
        """
        return (
            f"{edits} "
            f"([[User:BsoykaBot/Task {self.number}|Task {self.number}]], "
            f"v{__version__}, "
            "[[User talk:BsoykaBot|report errors]])"
        )
