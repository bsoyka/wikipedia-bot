import pywikibot
from pywikibot import pagegenerators

REPLACEMENTS = {
    "www-newspapers-com.wikipedialibrary.idm.oclc.org": "www.newspapers.com",
    "www.newspapers.com.wikipedialibrary.idm.oclc.org": "www.newspapers.com",
}

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
