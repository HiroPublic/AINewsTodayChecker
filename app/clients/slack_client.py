"""Slack Incoming Webhook client."""

import logging

import httpx


LOGGER = logging.getLogger(__name__)


class SlackClient:
    """Minimal Slack client with a small, explicit surface area."""

    def __init__(self, webhook_url: str, timeout: float = 10.0) -> None:
        self._webhook_url = webhook_url
        self._timeout = timeout

    def post_message(self, text: str) -> None:
        """Post a single text message to the configured webhook."""

        payload = {"text": text}
        LOGGER.info("Sending Slack webhook message")
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(self._webhook_url, json=payload)
            response.raise_for_status()
