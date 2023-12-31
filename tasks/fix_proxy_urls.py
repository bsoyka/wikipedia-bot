"""Replaces proxy domains from Wikipedia Library.

See https://en.wikipedia.org/wiki/User:BsoykaBot/Task_2 for more info.
"""

import pywikibot
from pywikibot import pagegenerators

REPLACEMENTS = {
    "www-newspapers-com.wikipedialibrary.idm.oclc.org": "www.newspapers.com",
    "www.newspapers.com.wikipedialibrary.idm.oclc.org": "www.newspapers.com",
}


def process_page(page: pywikibot.Page) -> None:
    """Processes a page."""
    text = page.text
    for proxy_string, replacement in REPLACEMENTS.items():
        text = text.replace(proxy_string, replacement)

    if text != page.text:
        page.text = text
        page.save(
            summary="Replacing [[WP:TWL|TWL]] proxy links ([[User:BsoykaBot/Task 2|Task 2]])",
            minor=False,
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
