from __future__ import annotations

"""Structured logging configuration for J.A.R.V.I.S. Mark V."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configures structured console logging with ISO-like timestamps and module names.

    Args:
        level: Minimum logging level (default: logging.INFO).
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is invoked multiple times
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]
