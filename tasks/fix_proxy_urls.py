"""Replaces proxy domains from Wikipedia Library.

See https://en.wikipedia.org/wiki/User:BsoykaBot/Task_2 for more info.
"""

import logging

import pywikibot
from loguru import logger
from pywikibot import pagegenerators

__version__ = "0.1.0"


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward Loguru."""

    def emit(self, record):
        """Send standard logging messages to Loguru."""
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Forward the message
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0)

REPLACEMENTS = {
    "www-newspapers-com.wikipedialibrary.idm.oclc.org": "www.newspapers.com",
    "www.newspapers.com.wikipedialibrary.idm.oclc.org": "www.newspapers.com",
    "doi-org.wikipedialibrary.idm.oclc.org": "doi.org",
    "doi.org.wikipedialibrary.idm.oclc.org": "doi.org",
    "www-jstor-org.wikipedialibrary.idm.oclc.org": "www.jstor.org",
    "www.jstor.org.wikipedialibrary.idm.oclc.org": "www.jstor.org",
}


def process_page(page: pywikibot.Page) -> None:
    """Processes a page."""
    text = page.text
    for proxy_string, replacement in REPLACEMENTS.items():
        text = text.replace(proxy_string, replacement)

    if text != page.text:
        page.text = text
        page.save(
            summary=f"Replacing [[WP:TWL|TWL]] proxy links ([[User:BsoykaBot/Task 2|Task 2]], v{__version__})",
            minor=True,
        )


def main():
    """Main script function."""
    pages_to_edit: set[pywikibot.Page] = set()

    for proxy_string in REPLACEMENTS:
        new_pages = set(
            pagegenerators.SearchPageGenerator(
                f'insource:"{proxy_string}"',
                namespaces={
                    0,
                },
            )
        )
        pages_to_edit.update(new_pages)

    for page in pages_to_edit:
        process_page(page)


if __name__ == "__main__":
    main()
