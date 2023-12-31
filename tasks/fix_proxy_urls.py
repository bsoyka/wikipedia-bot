"""Replaces proxy domains from Wikipedia Library.

See https://en.wikipedia.org/wiki/User:BsoykaBot/Task_2 for more info.
"""

import pywikibot
from pywikibot import pagegenerators

REPLACEMENTS = {
    "www-newspapers-com.wikipedialibrary.idm.oclc.org": "www.newspapers.com",
    "www.newspapers.com.wikipedialibrary.idm.oclc.org": "www.newspapers.com",
}


def main():
    site = pywikibot.Site()

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
        for find, replace in REPLACEMENTS.items():
            page.text = page.text.replace(find, replace)

        page.save(
            "Replacing [[WP:TWL|TWL]] proxy links ([[User:BsoykaBot/Task 2|Task 2]])",
            minor=True,
        )


if __name__ == "__main__":
    main()
