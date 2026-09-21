"""Replaces proxy domains from Wikipedia Library.

See https://en.wikipedia.org/wiki/User:BsoykaBot/Task_2 for more info.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from pywikibot import pagegenerators

from bsoykabot.tasks import Discovered, Task

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pywikibot

PROXY_CONFIG_PATH = Path(__file__).parent / 'proxy_config_domains.txt'


def _parse_domains(*, proxy_config: list[str] | None = None) -> set[str]:
    """Parse the domains to replace.

    Args:
        proxy_config: Optional list of lines from the proxy config file.
            If not provided, it will read from the default file.

    Returns:
        A set of domains to replace in the format 'domain.com'.
    """
    if proxy_config is None:
        proxy_config = PROXY_CONFIG_PATH.read_text().splitlines()

    result = set()

    for raw_line in proxy_config:
        line = raw_line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue

        # Host name lines
        if line.startswith('H'):
            url = line.split(' ')[1]

            if '/' in url:
                # Get just the domain
                parsed_domain = urlparse(url).netloc

                if parsed_domain:
                    result.add(parsed_domain)
            else:
                result.add(url)

        # Domain name lines
        elif line.startswith('D'):
            domain = line.split(' ')[1]

            result.add(domain)

            if not domain.startswith('www.'):
                result.add('www.' + domain)

    return result


@cache
def _replacements() -> tuple[tuple[str, str], ...]:
    """Build the proxy-string-to-domain replacements, longest string first.

    Cached so the config file is parsed, and the replacement map built,
    once per process rather than on every page -- a cold-start cost on
    Lambda instead of a per-page one.

    Returns:
        Pairs of (proxy string, replacement domain), sorted so a longer
        proxy string is always tried before any of its substrings.
    """
    domains = _parse_domains()

    replacements: dict[str, str] = {}
    for domain in domains:
        replacements[domain.replace('.', '-') + '.wikipedialibrary.idm.oclc.org'] = (
            domain
        )
        replacements[domain + '.wikipedialibrary.idm.oclc.org'] = domain

    return tuple(
        sorted(replacements.items(), key=lambda pair: len(pair[0]), reverse=True),
    )


class ProxyUrlsTask(Task):
    """Task to replace Wikipedia Library proxy URLs in articles."""

    name = 'proxy_urls'
    number = 2
    edit_summary_text = 'Replacing [[WP:TWL|TWL]] proxy links'

    def discover(  # ruff: ignore[no-self-use] -- part of the Task interface, not a free function
        self,
        cursor: str | None = None,
    ) -> Iterator[Discovered]:
        """Yield articles containing Wikipedia Library proxy URLs.

        Args:
            cursor: Ignored; this task's discovery is cheap enough to
                restart from the beginning every time.

        Yields:
            Each article containing a proxy URL.
        """
        del cursor

        for page in pagegenerators.SearchPageGenerator(
            'insource:"wikipedialibrary.idm.oclc.org"',
            namespaces={0},
        ):
            yield Discovered(title=page.title())

    def handle(self, page: pywikibot.Page) -> str | None:  # ruff: ignore[no-self-use]
        """Replace proxy URLs in a page with their original domains.

        Args:
            page: The page to inspect.

        Returns:
            The new page text, or None if no proxy URLs were found.
        """
        original: str = page.text
        text = original

        for proxy_string, replacement in _replacements():
            if proxy_string in text:
                text = text.replace(proxy_string, replacement)

        return text if text != original else None
