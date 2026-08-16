"""Test cases for the fix_proxy_urls task."""

from unittest.mock import Mock

from bsoykabot.tasks.proxy_urls import ProxyUrlsTask, _parse_domains, _replacements


def test_parse_domains() -> None:
    """Test that _parse_domains correctly extracts domains from the config."""
    # Create a mock proxy config
    mock_proxy_config = [
        'H https://host-without-www.com',
        'H https://www.host-with-www.com',
        'H host-no-slash.com',
        'H invalid/url',
        'D domain-without-www.com',
        'D www.domain-with-www.com',
        '# Comment',
        '',
    ]

    assert _parse_domains(proxy_config=mock_proxy_config) == {
        'host-without-www.com',
        'www.host-with-www.com',
        'host-no-slash.com',
        'domain-without-www.com',
        'www.domain-without-www.com',
        'www.domain-with-www.com',
    }


def _make_page(text: str) -> Mock:
    """Build a mock pywikibot.Page with the given text.

    Args:
        text: The page's wikitext.

    Returns:
        A mock page.
    """
    page = Mock()
    page.text = text
    return page


def test_handle_replaces_proxy_url() -> None:
    """Test that handle replaces a proxy URL with the original domain."""
    task = ProxyUrlsTask()
    page = _make_page('www-newspapers-com.wikipedialibrary.idm.oclc.org')

    result = task.handle(page)

    assert result == 'www.newspapers.com'


def test_handle_no_change() -> None:
    """Test that handle returns None if no proxy URLs are present."""
    task = ProxyUrlsTask()
    page = _make_page('www.example.com')

    assert task.handle(page) is None


def test_handle_is_idempotent() -> None:
    """Test that handling already-fixed text produces no further edit.

    This is the property that makes an SQS redelivery harmless rather than
    a duplicate edit: after one pass, no proxied hostname remains in the
    text, so a second pass must be a no-op.
    """
    task = ProxyUrlsTask()
    already_fixed = _make_page('www.newspapers.com')

    assert task.handle(already_fixed) is None


def test_replacements_are_sorted_longest_first() -> None:
    """Test that _replacements orders pairs by descending key length.

    Longer proxy strings must be tried before any of their substrings, or a
    shorter match could partially replace a longer one.
    """
    pairs = _replacements()
    lengths = [len(proxy_string) for proxy_string, _ in pairs]

    assert lengths == sorted(lengths, reverse=True)
