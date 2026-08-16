"""Pywikibot session management for BsoykaBot.

Pywikibot resolves its configuration directory the first time it is
imported anywhere in the process (see :mod:`pywikibot.config`), and on AWS
Lambda there is nothing on disk until this package puts it there. This
package's own initialization -- which always runs before any of its
submodules, including :mod:`bsoykabot.wiki.site`, the only place that
actually imports pywikibot -- writes the credential files first, so that
guarantee holds regardless of it.

Every other part of BsoykaBot that needs pywikibot (the task
implementations included) gets it only after importing something from this
package or one of its submodules, directly or transitively. That is what
keeps the ordering correct regardless of how ruff's isort arranges any
particular file's own import statements: Python always finishes
initializing a package before it imports any of that package's submodules,
and that guarantee -- unlike import statement order within a single file --
isn't something a formatter can rearrange.
"""

from bsoykabot.wiki._bootstrap import bootstrap

bootstrap()
