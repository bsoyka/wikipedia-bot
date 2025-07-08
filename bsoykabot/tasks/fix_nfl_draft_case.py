"""Fixes linked miscapitalization of "NFL draft" in articles.

See https://en.wikipedia.org/wiki/User:BsoykaBot/Task_3 for more info.
"""

import logging
import re
from pathlib import Path

import mwparserfromhell
import pywikibot
from loguru import logger
from pywikibot import pagegenerators

from bsoykabot._utils import create_edit_summary

LINK_FILE_PATH = Path(__file__).parent / "links_to_redirects.txt"
PAGES_PER_BATCH = 1_000


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Send standard logging messages to Loguru."""
        # Ignore DEBUG level messages
        if record.levelno < logging.INFO:
            return

        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Forward the message
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0)


def get_redirect_pages() -> set[pywikibot.Page]:
    """Make a set of all capitalized NFL Draft pages to change."""
    titles = {f"{year} NFL Draft" for year in range(1936, 2025)}
    pages = set(pagegenerators.PagesFromTitlesGenerator(titles))

    pages.update(
        pagegenerators.SearchPageGenerator(
            "intitle:/List of .+ in the NFL Draft/",
            namespaces=[0],
        ),
    )

    return set(pages)


def get_links_to_redirects(redirect_pages: set[pywikibot.Page]) -> set[pywikibot.Page]:
    """Get all pages that link to the redirect pages."""
    backlinks = set()

    for redirect in redirect_pages:
        backlinks.update(redirect.backlinks(namespaces=[0]))

    return backlinks


def fix_links_in_page(page: pywikibot.Page) -> str:  # noqa: PLR0912
    """Fix miscapitalized links to "NFL Draft" redirects in a page."""
    non_cosmetic_changes = False

    text = page.text
    wikicode = mwparserfromhell.parse(text)

    links: list[mwparserfromhell.nodes.wikilink.Wikilink] = wikicode.filter_wikilinks()

    for link in links:
        old_link_text: mwparserfromhell.Wikicode | None = link.text

        # Match link title to regex for "YEAR NFL Draft"
        if re.match(r"\d{4} NFL Draft", str(link.title)) or re.match(
            r"List of .+ in the NFL Draft",
            str(link.title),
        ):
            # Check if the link title is a redirect
            target = pywikibot.Page(page.site, link.title)
            if target.isRedirectPage():
                if "#" in str(link.title):
                    section_heading = str(link.title).split("#")[1]
                    new_page_title = str(target.getRedirectTarget().title())

                    link.title = f"{new_page_title}#{section_heading}"
                else:
                    new_page_title = str(target.getRedirectTarget().title())
                    link.title = new_page_title

                # Lowercase "Draft" in the link text if needed using regex
                if link.text:
                    link.text = re.sub(r"\bDraft\b", "draft", str(link.text))

                if (not link.text) or old_link_text != link.text:
                    non_cosmetic_changes = True

    templates: list[mwparserfromhell.nodes.template.Template] = (
        wikicode.filter_templates()
    )

    for template in templates:
        # Fix capitalization in {{Main|...}}, {{See also|...}}, etc.
        if template.name.matches({"Main", "See also", "Further"}):
            for param in template.params:
                if re.match(r"\d{4} NFL Draft", str(param.value)) or re.match(
                    r"List of .+ in the NFL Draft",
                    str(param.value),
                ):
                    # Check if the link title is a redirect
                    target = pywikibot.Page(page.site, param.value)
                    if target.isRedirectPage():
                        new_page_title = str(target.getRedirectTarget().title())
                        param.value = new_page_title

                        non_cosmetic_changes = True

    if non_cosmetic_changes:
        return str(wikicode)

    return text


def main(*, create_file: bool = False) -> None:
    """Run NFL draft case fixer."""
    if create_file:
        redirect_pages = get_redirect_pages()
        logger.info(f"Found {len(redirect_pages)} redirect pages")

        links_to_redirects = get_links_to_redirects(redirect_pages)
        logger.info(f"Found {len(links_to_redirects)} links to redirect pages")

        LINK_FILE_PATH.write_text(
            "\n".join(page.title() for page in links_to_redirects), encoding="utf-8"
        )

        logger.success(
            "Successfully created links_to_redirects.txt with links to redirect pages",
        )

        return

    # Get links from file
    if not LINK_FILE_PATH.exists():
        logger.error(
            f"Link file does not exist. Run the script with --create-file to create it."
        )
        return

    link_titles = LINK_FILE_PATH.read_text(encoding="utf-8").splitlines()
    links_to_redirects = [
        pywikibot.Page(pywikibot.Site("en", "wikipedia"), title.strip())
        for title in link_titles
    ]

    logger.info(f"Loaded {len(links_to_redirects)} pages to edit")

    edited_pages = 0

    while len(links_to_redirects) > 0:
        page = links_to_redirects.pop(0)

        if edited_pages >= PAGES_PER_BATCH:
            break

        old_text = page.text

        text = fix_links_in_page(page)
        page.text = text

        if text != old_text:
            logger.debug(f"Changes made to {page.title()}")
            try:
                page.save(
                    summary=create_edit_summary(
                        "Fixing miscapitalization of NFL draft links",
                        task=3,
                    ),
                    minor=True,
                )
                edited_pages += 1
            except pywikibot.exceptions.OtherPageSaveError as error:
                logger.warning(f"Skipping page {page.title()}: {error}")

        # Update the links file
        LINK_FILE_PATH.write_text(
            "\n".join(page.title() for page in links_to_redirects), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
