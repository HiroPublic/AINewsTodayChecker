"""Dependency builders for API routes."""

from app.clients.podcast_client import PodcastClient
from app.clients.slack_client import SlackClient
from app.core.config import get_settings
from app.notifier.slack import SlackNotifier
from app.persistence.state_store import StateStore
from app.services.fetch_service import FetchService
from app.services.job_service import JobService
from app.services.normalize_service import NormalizeService


def get_job_service() -> JobService:
    """Build a fresh job service for API calls."""

    settings = get_settings()
    notifier = None
    if settings.slack_webhook_url:
        notifier = SlackNotifier(client=SlackClient(webhook_url=settings.slack_webhook_url))
    return JobService(
        fetch_service=FetchService(
            PodcastClient(
                rss_url=settings.podcast_rss_url,
                apple_podcast_id=settings.podcast_apple_podcast_id,
            )
        ),
        normalize_service=NormalizeService(),
        state_store=StateStore(settings.state_file_path),
        slack_notifier=notifier,
        notify_score_threshold=settings.notify_score_threshold,
    )
