"""
Centralised file logger for Darklightz Lead Generator.

Writes all errors and info messages to:
    ~/.darklightz/app.log

Rotates at 5 MB, keeps 3 backups.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path

_LOG_DIR  = Path.home() / ".darklightz"
_LOG_PATH = _LOG_DIR / "app.log"

# Module-level logger — import and use this everywhere
logger: logging.Logger


def _setup() -> logging.Logger:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    _logger = logging.getLogger("darklightz")
    _logger.setLevel(logging.DEBUG)

    if _logger.handlers:          # already configured (e.g. re-imported)
        return _logger

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(
        _LOG_PATH,
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    _logger.addHandler(fh)

    # Console handler (visible when running from terminal)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)
    _logger.addHandler(ch)

    return _logger


logger = _setup()


def log_path() -> str:
    """Return the absolute path to the current log file."""
    return str(_LOG_PATH)
