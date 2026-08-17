"""Materialize Pywikibot's credential files before Pywikibot is imported.

Pywikibot resolves its configuration directory -- and therefore whether it
can find any credentials at all -- at import time; see
:mod:`bsoykabot.wiki` for the ordering guarantee this module relies on. On
AWS Lambda, nothing is on disk between cold starts except whatever this
module writes to ``/tmp``, so :func:`bootstrap` must run, and complete,
before pywikibot is imported anywhere in the process.

This module must not import pywikibot, directly or transitively.
"""

import json
import os
import stat
from pathlib import Path

import boto3

_DEFAULT_PYWIKIBOT_DIR = '/tmp/pywikibot'  # noqa: S108 -- the only writable path on Lambda
_PRIVATE_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR  # 0o600, as Pywikibot requires


def bootstrap() -> None:
    """Materialize Pywikibot's configuration files under a writable directory.

    A no-op locally, where ``BSOYKABOT_CREDENTIALS_SECRET`` isn't set and
    Pywikibot falls back to ``~/.pywikibot`` as usual, and a no-op on a warm
    Lambda invocation, where the files already exist from a previous
    invocation in the same execution environment.

    Raises:
        RuntimeError: If the files are missing immediately after writing
            them. Pywikibot fails silently on a missing user-config.py once
            it's installed in site-packages, which it always is on Lambda,
            so this has to be checked explicitly here -- see
            ``bsoykabot.wiki.site.get_site`` for the second half of that
            guard.
    """
    secret_id = os.environ.get('BSOYKABOT_CREDENTIALS_SECRET')
    if secret_id is None:
        return

    directory = Path(os.environ.get('PYWIKIBOT_DIR', _DEFAULT_PYWIKIBOT_DIR))
    config_file = directory / 'user-config.py'
    password_file = directory / 'user-password.py'

    if config_file.exists() and password_file.exists():
        return

    credentials = _fetch_credentials(secret_id)

    directory.mkdir(parents=True, exist_ok=True)
    _write_private(config_file, _render_user_config(credentials['username']))
    _write_private(password_file, _render_password_file(credentials))

    if not (config_file.exists() and password_file.exists()):
        msg = f'Failed to write Pywikibot configuration files to {directory}.'
        raise RuntimeError(msg)


def _fetch_credentials(secret_id: str) -> dict[str, str]:
    """Fetch the bot's Wikipedia credentials from Secrets Manager.

    Args:
        secret_id: The name or ARN of the secret holding the credentials.

    Returns:
        A mapping with 'username', 'bot_name', and 'bot_password' keys.
    """
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_id)
    payload: dict[str, str] = json.loads(response['SecretString'])
    return payload


def _write_private(path: Path, content: str) -> None:
    """Write a file that is readable and writable only by its owner.

    Pywikibot refuses to load credential files that are writable by anyone
    else, so the correct mode has to be set at creation time rather than
    applied afterwards with a separate chmod.

    Args:
        path: The file to write.
        content: The file's contents.
    """
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        _PRIVATE_FILE_MODE,
    )

    with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
        handle.write(content)


def _render_user_config(username: str) -> str:
    """Render the contents of Pywikibot's ``user-config.py``.

    Args:
        username: The bot's main Wikipedia account username.

    Returns:
        The rendered file contents.
    """
    put_throttle = os.environ.get('BSOYKABOT_PUT_THROTTLE', '10')
    simulate = os.environ.get('BSOYKABOT_SIMULATE', '0') == '1'

    return (
        "family = 'wikipedia'\n"
        "mylang = 'en'\n"
        f"usernames['wikipedia']['en'] = {username!r}\n"
        "password_file = 'user-password.py'\n"
        f'put_throttle = {put_throttle}\n'
        'maxlag = 5\n'
        'max_retries = 3\n'
        'retry_wait = 5\n'
        f'simulate = {simulate!r}\n'
        'user_agent_description = (\n'
        "    'BsoykaBot on AWS Lambda; '\n"
        "    'https://en.wikipedia.org/wiki/User:BsoykaBot'\n"
        ')\n'
    )


def _render_password_file(credentials: dict[str, str]) -> str:
    """Render the contents of Pywikibot's ``user-password.py``.

    Uses a `BotPassword
    <https://www.mediawiki.org/wiki/Special:BotPasswords>`_ entry rather
    than the main account password, so the credential stored in Secrets
    Manager can be scoped and revoked independently of the main account.

    Args:
        credentials: The bot's Wikipedia credentials.

    Returns:
        The rendered file contents.
    """
    username = credentials['username']
    bot_name = credentials['bot_name']
    bot_password = credentials['bot_password']

    return f'({username!r}, BotPassword({bot_name!r}, {bot_password!r}))\n'
