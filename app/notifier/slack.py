"""Slack notification facade kept replaceable for external project parity."""

from app.clients.slack_client import SlackClient


class SlackNotifier:
    """Facade around Slack webhook delivery."""

    def __init__(self, client: SlackClient) -> None:
        self._client = client

    def notify_messages(self, messages: list[str]) -> None:
        """Send up to three messages in sequence."""

        for message in messages[:3]:
            self._client.post_message(text=message)
