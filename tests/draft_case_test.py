"""Test cases for the fix_nfl_draft_case task."""

from datetime import UTC, datetime
from pathlib import Path

from bsoykabot.tasks.draft_case import (
    LINK_FILE_PATH,
    PAGES_PER_BATCH,
    _redirect_titles,
)


def test_task_constants() -> None:
    """Test that task constants are defined correctly."""
    assert isinstance(LINK_FILE_PATH, Path), (
        'LINK_FILE_PATH should be a pathlib.Path object'
    )
    assert LINK_FILE_PATH.is_absolute(), 'LINK_FILE_PATH should be an absolute path'
    assert LINK_FILE_PATH.suffix == '.txt', 'LINK_FILE_PATH should have a .txt suffix'

    assert isinstance(PAGES_PER_BATCH, int), 'PAGES_PER_BATCH should be an integer'
    assert PAGES_PER_BATCH > 0, 'PAGES_PER_BATCH should be positive'


def test_redirect_titles() -> None:
    """Test that _redirect_titles covers the expected year range.

    This is a pure, offline test on purpose: the year range previously
    shipped as a hardcoded ``range(1936, 2025)`` and silently went stale
    once 2025 passed, so the coverage that matters here is the range
    itself, not a live Wikipedia lookup.
    """
    titles = _redirect_titles()

    assert isinstance(titles, set), '_redirect_titles should return a set'
    assert '1936 NFL Draft' in titles, 'the earliest draft year should be included'
    assert '1935 NFL Draft' not in titles, 'years before the first draft are excluded'

    current_year = datetime.now(tz=UTC).year
    assert f'{current_year} NFL Draft' in titles, (
        "this year's draft should be included"
    )
    assert f'{current_year + 1} NFL Draft' in titles, (
        "next year's draft is usually created in advance"
    )
    assert f'{current_year + 2} NFL Draft' not in titles, (
        'the range should not reach two years out'
    )
