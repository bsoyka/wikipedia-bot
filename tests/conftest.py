"""Configuration for pytest fixtures."""

import pytest
from loguru import logger


@pytest.fixture(autouse=True)
def silence_loguru() -> None:
    """Silence loguru during tests."""
    logger.remove()
