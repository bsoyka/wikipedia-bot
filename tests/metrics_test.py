"""Test cases for the EMF metrics helpers."""

import json

import pytest

from bsoykabot.aws.metrics import emit_page_outcome, emit_pages_discovered


def _last_emf_document(capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    """Parse the most recently printed line as an EMF document.

    Args:
        capsys: The pytest fixture capturing stdout/stderr.

    Returns:
        The parsed JSON document.
    """
    out = capsys.readouterr().out.strip().splitlines()
    return json.loads(out[-1])  # type: ignore[no-any-return]


def test_emit_page_outcome_marks_only_the_given_outcome(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that only the reported outcome's counter is set to 1."""
    emit_page_outcome('proxy_urls', 'edited')
    document = _last_emf_document(capsys)

    assert document['Task'] == 'proxy_urls'
    assert document['PagesEdited'] == 1
    assert document['PagesNoChange'] == 0
    assert document['PagesBlocked'] == 0
    assert document['PagesError'] == 0


def test_emit_page_outcome_is_valid_emf(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that the printed document has the shape CloudWatch expects."""
    emit_page_outcome('draft_case', 'error')
    document = _last_emf_document(capsys)

    aws = document['_aws']
    assert isinstance(aws, dict)
    metric_directives = aws['CloudWatchMetrics']
    assert isinstance(metric_directives, list)
    directive = metric_directives[0]

    assert directive['Namespace'] == 'BsoykaBot'
    assert directive['Dimensions'] == [['Task']]
    metric_names = {metric['Name'] for metric in directive['Metrics']}
    assert metric_names == {
        'PagesEdited',
        'PagesNoChange',
        'PagesBlocked',
        'PagesError',
    }


def test_emit_pages_discovered(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that emit_pages_discovered reports the given count."""
    emit_pages_discovered('draft_case', 42)
    document = _last_emf_document(capsys)

    assert document['Task'] == 'draft_case'
    assert document['PagesDiscovered'] == 42
