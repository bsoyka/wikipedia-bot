"""Pywikibot session management for BsoykaBot.

Pywikibot resolves its configuration directory the first time it is
imported anywhere in the process (see :mod:`pywikibot.config`), and on AWS
Lambda there is nothing on disk until this package puts it there.

The bootstrap actually has to run here, at package init, rather than
per-module: several modules (:mod:`bsoykabot.tasks.draft_case`,
:mod:`bsoykabot.wiki.site`, :mod:`bsoykabot.wiki.editor`,
:mod:`bsoykabot.runner`, :mod:`bsoykabot.aws.handlers`) import pywikibot
directly at module scope, and ruff's isort always sorts a bare
``import pywikibot`` above a ``from bsoykabot... import`` line, since
pywikibot is third-party and bsoykabot is first-party. A bootstrap call
placed in any one of those files would only protect that file's own late
imports, not a sibling module's early one.

What actually makes this safe regardless of import order or which module
happens to run first is that :mod:`bsoykabot` itself -- the top-level
package -- imports this package at the top of its own ``__init__.py``.
Python always finishes initializing a package before importing any of that
package's submodules, all the way up the chain, so importing *anything*
under ``bsoykabot`` runs :mod:`bsoykabot`'s own init, which runs this
package's init, which calls :func:`bootstrap`, before that submodule's own
body -- and its own ``import pywikibot`` -- ever executes. That guarantee,
unlike import order within a single file, isn't something a formatter can
rearrange.
"""

from bsoykabot.wiki._bootstrap import bootstrap

bootstrap()
