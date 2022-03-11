import re
from typing import Iterable

import pywikibot
from pywikibot import pagegenerators

site = pywikibot.Site()
cat = pywikibot.Category(site, "Category:CS1 maint: PMC format")

gen: Iterable[pywikibot.Page] = pagegenerators.CategorizedPageGenerator(cat)

for page in gen:
    page.text = re.sub(r"\| *pmc *= *pmc", r"|pmc=", page.text, flags=re.IGNORECASE)
    page.save("Fixing PMC format", minor=True)
