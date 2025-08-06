"""Test cases for the fix_proxy_urls task."""

from unittest.mock import Mock

from pywikibot.exceptions import OtherPageSaveError

from bsoykabot.tasks import Task
from bsoykabot.tasks.proxy_urls import _parse_domains, _process_page

TEST_REPLACEMENTS = {
    'www-newspapers-com.wikipedialibrary.idm.oclc.org': 'www.newspapers.com'
}


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


def test_process_page() -> None:
    """Test that _process_page correctly replaces proxy URLs."""
    # Create a mock Task object
    mock_task = Mock(spec=Task)

    # Create a mock page
    mock_page = Mock()
    mock_page.text = 'www-newspapers-com.wikipedialibrary.idm.oclc.org'

    # Call the function with the mock page
    _process_page(mock_page, TEST_REPLACEMENTS, task=mock_task)

    # Check that the page's text was updated and saved
    assert mock_page.text == 'www.newspapers.com'
    mock_page.save.assert_called_once()


def test_process_page_no_change() -> None:
    """Test that _process_page does not change text if no proxy URLs are present."""
    # Create a mock Task object
    mock_task = Mock(spec=Task)

    # Create a mock page
    mock_page = Mock()
    mock_page.text = 'www.example.com'

    # Call the function with the mock page
    _process_page(mock_page, TEST_REPLACEMENTS, task=mock_task)

    # Check that the page's text was not updated and the page was not saved
    assert mock_page.text == 'www.example.com'
    mock_page.save.assert_not_called()


def test_process_page_save_error() -> None:
    """Test that _process_page gracefully handles a save error."""
    # Create a mock Task object
    mock_task = Mock(spec=Task)

    # Create a mock page
    mock_page = Mock()
    mock_page.text = 'www-newspapers-com.wikipedialibrary.idm.oclc.org'
    mock_page.save.side_effect = OtherPageSaveError(page=mock_page, reason='Error')

    # Call the function with the mock page
    _process_page(mock_page, TEST_REPLACEMENTS, task=mock_task)

    # Check that the page's text was updated and saved
    assert mock_page.text == 'www.newspapers.com'
    mock_page.save.assert_called_once()
