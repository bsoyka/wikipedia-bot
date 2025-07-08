"""Test cases for the fix_nfl_draft_case task."""

from pathlib import Path

from pywikibot import Page

from bsoykabot.tasks.draft_case import (
    LINK_FILE_PATH,
    PAGES_PER_BATCH,
    _get_redirect_pages,
)


def test_task_constants() -> None:
    """Test that task constants are defined correctly."""
    assert isinstance(LINK_FILE_PATH, Path), (
        "LINK_FILE_PATH should be a pathlib.Path object"
    )
    assert LINK_FILE_PATH.is_absolute(), "LINK_FILE_PATH should be an absolute path"
    assert LINK_FILE_PATH.suffix == ".txt", "LINK_FILE_PATH should have a .txt suffix"

    assert isinstance(PAGES_PER_BATCH, int), "PAGES_PER_BATCH should be an integer"
    assert PAGES_PER_BATCH > 0, "PAGES_PER_BATCH should be positive"


def test_get_redirect_pages() -> None:
    """Test that _get_redirect_pages returns a set of pages."""
    redirect_pages = _get_redirect_pages()

    assert isinstance(redirect_pages, set), "_get_redirect_pages should return a set"
    assert len(redirect_pages) > 0, "_get_redirect_pages should return non-empty set"

    assert all(isinstance(page, Page) for page in redirect_pages), (
        "All items in the set should be pywikibot.Page objects"
    )
    assert all("NFL Draft" in page.title() for page in redirect_pages), (
        "All pages should include capitalized 'NFL Draft' in their titles"
    )
