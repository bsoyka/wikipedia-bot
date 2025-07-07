# Contributing to BsoykaBot

BsoykaBot is a bot that runs on the English Wikipedia, performing various
maintenance tasks. This document outlines how you can contribute to the bot's
development, including what contributions are welcome and how to get started.

This is a project for the community, and help from the community is always
greatly appreciated. Whether you're a seasoned developer or just curious about
how things work around here, there are plenty of ways to lend a hand.

## How the bot works

BsoykaBot is built using Python and the
[Pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot) framework, which
provides tools for interacting with MediaWiki-based wikis, including Wikipedia.

As [approved by the community](https://en.wikipedia.org/wiki/Wikipedia:Bots/Requests_for_approval), the bot performs various tasks, each on a different schedule. For information on the bot's tasks, see [its user page on Wikipedia](https://en.wikipedia.org/wiki/User:BsoykaBot).

Generally, BsoykaBot's tasks are relatively simple scripts run as cron jobs. These scripts are invoked through the [`tasks/__main__.py`](tasks/__main__.py) file, which serves as a general entry point for the bot's tasks and passes the appropriate arguments to the task scripts.

## How you can help

Per Wikipedia's policies, new bot tasks must generally be approved by the community through the [Bot Request for Approval (BRFA)](https://en.wikipedia.org/wiki/Wikipedia:Bots/Requests_for_approval) process.

## Setting up a development environment

## Code review and deployment
