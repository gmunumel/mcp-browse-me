"""Centralized logging setup for the project."""

from __future__ import annotations

import logging


def _get_logger(name: str) -> logging.Logger:
    """Return a logger with default formatting configured once."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    return logging.getLogger(name)


# Default logger for modules that prefer importing the shared instance.
logger = _get_logger(__name__)
