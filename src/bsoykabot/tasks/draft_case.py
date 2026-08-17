"""Fixes linked miscapitalization of "NFL draft" in articles.

See https://en.wikipedia.org/wiki/User:BsoykaBot/Task_3 for more info.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from functools import lru_cache
from typing import TYPE_CHECKING

import mwparserfromhell
import pywikibot
from pywikibot import pagegenerators

from bsoykabot.tasks import Discovered, Task
from bsoykabot.wiki.site import get_site

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pywikibot.site import APISite

FIRST_DRAFT_YEAR = 1936


def _redirect_titles() -> set[str]:
    """Build the titles of NFL Draft year-redirect pages to look up.

    Draft articles for the upcoming year are typically created a year in
    advance of the draft itself, so the range extends one year past the
    current year.

    Returns:
        A set of page titles, e.g. '2024 NFL Draft'.
    """
    current_year = datetime.now(tz=UTC).year

    return {f'{year} NFL Draft' for year in range(FIRST_DRAFT_YEAR, current_year + 2)}


def _list_redirect_titles() -> set[str]:
    """Find titles of "List of ... in the NFL Draft" redirect pages.

    Returns:
        A set of page titles found via search.
    """
    return {
        page.title()
        for page in pagegenerators.SearchPageGenerator(
            'intitle:/List of .+ in the NFL Draft/',
            namespaces=[0],
        )
    }


@lru_cache(maxsize=512)
def _resolve_redirect_target(site: APISite, title: str) -> str | None:
    """Resolve a redirect's target title, if the title is a redirect.

    Memoized because a batch of pages commonly links to the same handful of
    redirects repeatedly (e.g. many articles link to "2020 NFL Draft"), and
    each lookup is otherwise a network round trip.

    Args:
        site: The site the page belongs to.
        title: The title to resolve.

    Returns:
        The redirect's target title, or None if the page isn't a redirect.
    """
    target = pywikibot.Page(site, title)

    if target.isRedirectPage():
        return str(target.getRedirectTarget().title())

    return None


def _fix_links_in_page(page: pywikibot.Page) -> str:  # noqa: C901
    """Fix miscapitalized links to "NFL Draft" redirects in a page.

    Returns:
        The updated page text.
    """
    non_cosmetic_changes = False

    text: str = page.text
    wikicode = mwparserfromhell.parse(text)

    links: list[mwparserfromhell.nodes.wikilink.Wikilink] = wikicode.filter_wikilinks()

    for link in links:
        old_link_text: mwparserfromhell.wikicode.Wikicode | None = link.text

        # Match link title to regex for "YEAR NFL Draft"
        if re.match(r'\d{4} NFL Draft', str(link.title)) or re.match(
            r'List of .+ in the NFL Draft',
            str(link.title),
        ):
            link_title = str(link.title)
            section_heading = None
            lookup_title = link_title

            if '#' in link_title:
                lookup_title, section_heading = link_title.split('#', 1)

            new_page_title = _resolve_redirect_target(page.site, lookup_title)

            if new_page_title is not None:
                link.title = (
                    f'{new_page_title}#{section_heading}'
                    if section_heading
                    else new_page_title
                )

                # Lowercase "Draft" in the link text if needed using regex
                if link.text:
                    link.text = re.sub(r'\bDraft\b', 'draft', str(link.text))

                if (not link.text) or old_link_text != link.text:
                    non_cosmetic_changes = True

    templates: list[mwparserfromhell.nodes.template.Template] = (
        wikicode.filter_templates()
    )

    for template in templates:
        # Fix capitalization in {{Main|...}}, {{See also|...}}, etc.
        if template.name.matches({'Main', 'See also', 'Further'}):
            for param in template.params:
                if re.match(r'\d{4} NFL Draft', str(param.value)) or re.match(
                    r'List of .+ in the NFL Draft',
                    str(param.value),
                ):
                    new_page_title = _resolve_redirect_target(
                        page.site,
                        str(param.value),
                    )

                    if new_page_title is not None:
                        param.value = new_page_title
                        non_cosmetic_changes = True

    if non_cosmetic_changes:
        return str(wikicode)

    return text


class DraftCaseTask(Task):
    """Task to correct capitalization of "NFL draft" in articles."""

    name = 'draft_case'
    number = 3
    edit_summary_text = 'Fixing miscapitalization of NFL draft links'

    def discover(  # noqa: PLR6301 -- part of the Task interface, not a free function
        self,
        cursor: str | None = None,
    ) -> Iterator[Discovered]:
        """Yield articles linking to miscapitalized NFL draft redirects.

        Discovery resumes from a coarse cursor: the JSON-encoded list of
        redirect titles not yet processed. Resuming re-enumerates the
        backlinks of the redirect that was in progress when the cursor was
        taken; any pages yielded twice as a result are harmless, since
        handling this task's pages is idempotent (see
        ``tests/draft_case_test.py::test_handle_is_idempotent``).

        Args:
            cursor: A JSON-encoded list of redirect titles still to
                process, or None to start from the beginning.

        Yields:
            Each article that links to one of the redirects, paired with a
            cursor that resumes discovery with the redirects after the one
            currently being processed.
        """
        pending: list[str] = (
            json.loads(cursor)
            if cursor
            else sorted(_redirect_titles() | _list_redirect_titles())
        )

        site = get_site()

        while pending:
            title, *remaining = pending
            token = json.dumps(remaining) if remaining else None

            redirect = pywikibot.Page(site, title)
            for backlink in redirect.backlinks(namespaces=[0]):
                yield Discovered(title=backlink.title(), cursor=token)

            pending = remaining

    def handle(self, page: pywikibot.Page) -> str | None:  # noqa: PLR6301
        """Fix miscapitalized NFL draft links in a page.

        Args:
            page: The page to inspect.

        Returns:
            The new page text, or None if the page needs no edit.
        """
        text = _fix_links_in_page(page)
        return text if text != page.text else None
