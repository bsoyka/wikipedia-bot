"""Test cases for the fix_nfl_draft_case task."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from bsoykabot.tasks import draft_case
from bsoykabot.tasks.draft_case import DraftCaseTask, _redirect_titles


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
    assert f'{current_year} NFL Draft' in titles, "this year's draft should be included"
    assert f'{current_year + 1} NFL Draft' in titles, (
        "next year's draft is usually created in advance"
    )
    assert f'{current_year + 2} NFL Draft' not in titles, (
        'the range should not reach two years out'
    )


def _make_page(text: str) -> Mock:
    """Build a mock pywikibot.Page with the given text.

    Args:
        text: The page's wikitext.

    Returns:
        A mock page.
    """
    page = Mock()
    page.site = Mock()
    page.text = text
    return page


def test_handle_is_idempotent() -> None:
    """Test that handling already-fixed text produces no further edit.

    This is the property that makes an SQS redelivery harmless rather than
    a duplicate edit: once a link points directly at the (lowercase)
    article instead of the capitalized redirect, it no longer matches the
    pattern this task looks for, so a second pass must be a no-op. No
    redirect lookup happens here, so this stays offline.
    """
    task = DraftCaseTask()
    already_fixed = _make_page('The [[2020 NFL draft]] was held in April.')

    assert task.handle(already_fixed) is None


def test_handle_fixes_miscapitalized_link(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that handle rewrites a link to a miscapitalized redirect."""
    monkeypatch.setattr(
        draft_case,
        '_resolve_redirect_target',
        lambda site, title: '2020 NFL draft',  # ruff: ignore[unused-lambda-argument]
    )

    task = DraftCaseTask()
    page = _make_page('The [[2020 NFL Draft]] was held in April.')

    result = task.handle(page)

    assert result == 'The [[2020 NFL draft]] was held in April.'


def test_handle_leaves_non_redirect_links_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that handle makes no change when the link isn't a redirect."""
    monkeypatch.setattr(
        draft_case,
        '_resolve_redirect_target',
        lambda site, title: None,  # ruff: ignore[unused-lambda-argument]
    )

    task = DraftCaseTask()
    page = _make_page('The [[2020 NFL Draft]] was held in April.')

    assert task.handle(page) is None
