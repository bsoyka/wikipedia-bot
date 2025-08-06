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

Generally, BsoykaBot's tasks are relatively simple scripts run as cron jobs. These scripts are invoked through the [`bsoykabot/tasks/__main__.py`](src/bsoykabot/tasks/__main__.py) file, which serves as a general entry point for the bot's tasks and passes the appropriate arguments to the task scripts.

## How you can help

Per Wikipedia's policies, new bot tasks must generally be approved by the community through the [Bot Request for Approval (BRFA)](https://en.wikipedia.org/wiki/Wikipedia:Bots/Requests_for_approval) process.

However, a much easier way to contribute is to help improve BsoykaBot's existing tasks! Check out the list of open issues in this repository to see if there's anything you're interested in working on. If you find an issue you'd like to tackle:

1. **Comment on the issue** to let us the world you're working on it. This helps avoid duplicate efforts.
2. **Fork the repository** and create a new branch for your changes.
3. **Set up your development environment** (see below).
4. **Make your changes**, including applicable unit test updates. (If you're not sure how to write tests, don't worry! We can walk through it together.)
5. **Submit a pull request** with a clear description of what you've done and why. (Link to the issue you were working on, if applicable.)
6. **Wait for code review**, and we'll go from there!

## Setting up a development environment

Working on BsoykaBot requires a few tools behind the scenes. Here's a quick overview of each one, how to set it up, and how to use it:

### uv

uv is a Python package and project manager. We use it to handle Python versions, project dependencies, and virtual environments. You'll want to install uv before anything else listed here!

There are many ways to install uv—check out [their installation instructions](https://docs.astral.sh/uv/getting-started/installation/) to see what's easiest for your system.

Once you have uv installed, run the following command in the project directory to set up a virtual environment and install all necessary dependencies, including developer tools:
```shell
uv sync
```

This should also automatically install an appropriate Python version if one is not already installed.

Once you've set up your virtual environment with the previous command, you can use the `uv run` command to execute scripts and other commands within that environment. For further information, see [uv's documentation](https://docs.astral.sh/uv/reference/cli/#uv-run).

### Poe the Poet

Poe the Poet is a task runner set up to provide aliases for many commands you may need to run while working on BsoykaBot.

You can also install it globally using uv:
```shell
uv tool install poethepoet
```

This allows you to replace `uv run poe` in the examples throughout this document with only `poe`.

### Pywikibot

Pywikibot has a script to generate the necessary files to authenticate your bot. This command will guide you through creating the `user-config.py` and `user-password.py` files in the project directory:
```shell
uv run poe login
```

### pre-commit

pre-commit adds a few hooks to your Git configuration to run some style checks before you commit your changes. Set it up with this command:
```shell
uv run poe precommit
```

If you'd like to run the checks across all files in the repo on demand (rather than just those you've edited in your commit), run this command:
```shell
uv run poe check
```

### Commitizen

This project uses Commitizen to standardize commit messages. Stage your changes and commit using these commands:
```shell
git add .
poe commit
```

### Ruff

Much of the style-checking logic in the pre-commit hooks is provided by Ruff, a Python linter and code formatter.

To run Ruff's checks, auto-fixes, and formatting, use these commands:
```shell
uv run ruff check --fix
uv run ruff format
```

These commands are also included in the pre-commit hooks—they'll be run before every commit if you set that up in the previous section, and they'll run automatically on every pull request.

### Pytest

Unit testing is done with Pytest. See existing files in [`tests/`](tests) for examples on how this is done, and run the full suite of tests with this command:
```shell
uv run poe test
```

### Sentry

In production, errors are automatically tracked and logged using Sentry. There's no further setup needed in your environment, but it's a tool worth noting so you understand its presence.

## Code review and deployment

Once you make a pull request, you'll get automated feedback from a few services:

* **GitHub Copilot** will leave comments on your changes, which may include suggestions for further improvements. These are AI-generated and not always accurate, so take them with a grain of salt; however, they may offer helpful improvements.
* **pre-commit.ci** will run the same style checks mentioned previously (including Ruff), possibly including some automated fixes if needed.
* **CodeQL** will analyze your changes for any security issues, flagging them if needed.

As soon as possible, you'll see a human review from me, @bsoyka. If there are any other changes I'd like to see, I'll help you through them.

Once your pull request is fully approved, both by me and my army of robots, it'll be merged into the `main` branch. I'll update the bot's version number following the merge (using [Bump My Version](https://callowayproject.github.io/bump-my-version/)). A new tag/release will be created shortly after, triggering the new code to deploy to the bot's server.
