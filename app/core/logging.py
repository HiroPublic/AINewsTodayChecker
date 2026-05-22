"""Logging configuration helpers."""

import logging

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure root logging once for CLI and API execution."""

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # httpx INFO logs include the full request URL. Gemini passes the API key as
    # a query parameter, so keep third-party HTTP logs above INFO by default.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
