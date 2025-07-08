"""Test cases for the fix_proxy_urls task."""

from unittest.mock import Mock

from bsoykabot.tasks.fix_proxy_urls import process_page

TEST_REPLACEMENTS = {
    "www-newspapers-com.wikipedialibrary.idm.oclc.org": "www.newspapers.com"
}


def test_process_page() -> None:
    """Test that process_page correctly replaces proxy URLs."""
    # Create a mock page
    mock_page = Mock()
    mock_page.text = "www-newspapers-com.wikipedialibrary.idm.oclc.org"

    # Call the function with the mock page
    process_page(mock_page, TEST_REPLACEMENTS)

    # Check that the page's text was updated and saved
    assert mock_page.text == "www.newspapers.com"
    mock_page.save.assert_called_once()


def test_process_page_no_change() -> None:
    """Test that process_page does not change text if no proxy URLs are present."""
    # Create a mock page
    mock_page = Mock()
    mock_page.text = "www.example.com"

    # Call the function with the mock page
    process_page(mock_page, TEST_REPLACEMENTS)

    # Check that the page's text was not updated and the page was not saved
    assert mock_page.text == "www.example.com"
    mock_page.save.assert_not_called()
