"""Logging configuration helpers."""

import logging

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure root logging once for CLI and API execution."""

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
