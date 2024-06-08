"""Internal utilities shared between tasks."""


def create_edit_summary(edits: str, task: int, version: str) -> str:
    """Create an edit summary."""
    return (
        f"{edits} "
        f"([[User:BsoykaBot/Task {task}|Task {task}]] "
        f"v{version}, "
        "[[User talk:BsoykaBot|report errors]])"
    )
