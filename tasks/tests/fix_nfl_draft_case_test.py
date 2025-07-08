"""Test cases for the fix_nfl_draft_case task."""

from pathlib import Path

from tasks.fix_nfl_draft_case import LINK_FILE_PATH, PAGES_PER_BATCH


def test_task_constants() -> None:
    """Test that task constants are defined correctly."""
    assert isinstance(LINK_FILE_PATH, Path), (
        "LINK_FILE_PATH should be a pathlib.Path object"
    )
    assert LINK_FILE_PATH.is_absolute(), "LINK_FILE_PATH should be an absolute path"
    assert LINK_FILE_PATH.suffix == ".txt", "LINK_FILE_PATH should have a .txt suffix"

    assert isinstance(PAGES_PER_BATCH, int), "PAGES_PER_BATCH should be an integer"
    assert PAGES_PER_BATCH > 0, "PAGES_PER_BATCH should be positive"
