"""Structured logging configuration for the aoos_fishcount package."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(log_dir: str | Path | None = None, level: int = logging.INFO) -> None:
    """Configure root logger with console and optional file handlers.

    Args:
        log_dir: Directory to write rotating log files. If None, logs to console only.
        level: Logging level (default: INFO).
    """
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%S"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_dir is not None:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            Path(log_dir) / "fishcount.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
        )
        handlers.append(fh)

    logging.basicConfig(level=level, format=fmt, datefmt=datefmt, handlers=handlers)
