"""Replaces proxy domains from Wikipedia Library.

See https://en.wikipedia.org/wiki/User:BsoykaBot/Task_2 for more info.
"""

from pathlib import Path
from urllib.parse import urlparse

import pywikibot
from loguru import logger
from pywikibot import pagegenerators

from bsoykabot._utils import create_edit_summary


def parse_domains() -> set[str]:
    """Parse the domains to replace."""
    with (Path(__file__).parent / "proxy_config_domains.txt").open(
        encoding="utf-8"
    ) as file:
        result = set()

        for raw_line in file:
            line = raw_line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Host name lines
            if line.startswith("H"):
                url = line.split(" ")[1]

                if "/" in url:
                    # Get just the domain
                    parsed_domain = urlparse(url).netloc

                    if parsed_domain:
                        result.add(parsed_domain)
                else:
                    result.add(url)

            # Domain name lines
            elif line.startswith("D"):
                domain = line.split(" ")[1]

                result.add(domain)

                if not domain.startswith("www."):
                    result.add("www." + domain)

        return result


def process_page(page: pywikibot.Page, replacements: dict[str, str]) -> None:
    """Process a page."""
    text = page.text

    # Sort keys by length to avoid replacing substrings
    for proxy_string, replacement in sorted(
        replacements.items(),
        key=lambda x: len(x[0]),
        reverse=True,
    ):
        if proxy_string in text:
            text = text.replace(proxy_string, replacement)

    if text != page.text:
        page.text = text

        try:
            page.save(
                summary=create_edit_summary(
                    "Replacing [[WP:TWL|TWL]] proxy links",
                    task=2,
                ),
                minor=True,
            )
        except pywikibot.exceptions.OtherPageSaveError as error:
            logger.warning(f"Skipping page {page.title()}: {error}")


def main() -> None:
    """Run proxy URL fixer."""
    domains = parse_domains()
    logger.info(f"Parsed {len(domains)} domains")

    replacements = {}

    for domain in domains:
        replacements[domain.replace(".", "-") + ".wikipedialibrary.idm.oclc.org"] = (
            domain
        )
        replacements[domain + ".wikipedialibrary.idm.oclc.org"] = domain

    logger.info(f"Set up {len(replacements)} text replacements")

    pages_to_edit = set(
        pagegenerators.SearchPageGenerator(
            'insource:"wikipedialibrary.idm.oclc.org"',
            namespaces={0},
        ),
    )

    logger.info(f"Found {len(pages_to_edit)} pages to edit")

    for page in pages_to_edit:
        process_page(page, replacements)


if __name__ == "__main__":
    main()
