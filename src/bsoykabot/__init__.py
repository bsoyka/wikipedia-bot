"""Tasks run by BsoykaBot on the English Wikipedia."""

from importlib.metadata import version

# Bootstraps Pywikibot's credential files (see bsoykabot.wiki) before
# Pywikibot is ever imported. This has to live here, at the top of the
# `bsoykabot` package itself, rather than only in bsoykabot.tasks or
# bsoykabot.wiki: Python always finishes executing a package's __init__.py
# before importing any of that package's submodules, all the way up the
# chain, so importing *anything* under `bsoykabot` -- bsoykabot.runner,
# bsoykabot.aws.handlers, bsoykabot.cli, all of it -- runs this first,
# regardless of what that submodule's own import statements do or how
# ruff's isort orders them. A version of this that only lived in
# bsoykabot.tasks or bsoykabot.wiki would only protect their own
# submodules, not sibling modules like bsoykabot.runner and
# bsoykabot.aws.handlers that both import pywikibot directly at module
# scope -- which is exactly the bug this fixes.
from bsoykabot import wiki  # ruff: ignore[unused-import]

__version__ = version('bsoykabot')
