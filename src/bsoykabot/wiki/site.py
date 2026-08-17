"""The bot's Pywikibot session.

This is the only module in BsoykaBot that imports pywikibot at module
scope. Because it lives inside the ``bsoykabot.wiki`` package, importing it
-- from anywhere, in any order -- always runs ``bsoykabot/wiki/__init__.py``
first, which is what guarantees the credential bootstrap in
:mod:`bsoykabot.wiki._bootstrap` completes before pywikibot is ever
imported. See :mod:`bsoykabot.wiki` for the full explanation.
"""

from functools import lru_cache

import pywikibot


@lru_cache(maxsize=1)
def get_site() -> pywikibot.Site:
    """Return the bot's logged-in Pywikibot Site for English Wikipedia.

    Memoized so a warm Lambda invocation, or a single local run, reuses one
    authenticated session -- and its underlying HTTP connection -- instead
    of logging in again for every page.

    Returns:
        The authenticated Site.

    Raises:
        RuntimeError: If Pywikibot did not end up logged in, which should
            only happen if the credential bootstrap silently failed. It is
            treated as a hard stop rather than something to retry, since
            editing anonymously from here would look on-wiki like a
            compromised account.
    """
    site = pywikibot.Site('en', 'wikipedia')
    site.login()

    if not site.logged_in():
        msg = 'Pywikibot is not logged in; refusing to edit anonymously.'
        raise RuntimeError(msg)

    return site
