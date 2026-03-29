"""Dependency builders for API routes."""

from app.clients.podcast_client import PodcastClient
from app.clients.gemini_client import GeminiClient
from app.clients.perplexity_client import PerplexityClient
from app.clients.slack_client import SlackClient
from app.core.config import get_settings
from app.notifier.slack import SlackNotifier
from app.persistence.state_store import StateStore
from app.services.fetch_service import FetchService
from app.services.job_service import JobService
from app.services.normalize_service import NormalizeService
from app.services.verifier_service import EpisodeVerifierService


def get_job_service() -> JobService:
    """Build a fresh job service for API calls."""

    settings = get_settings()
    notifier = None
    if settings.slack_webhook_url:
        notifier = SlackNotifier(client=SlackClient(webhook_url=settings.slack_webhook_url))
    provider = settings.verifier_provider.strip().lower()
    return JobService(
        fetch_service=FetchService(
            PodcastClient(
                rss_url=settings.podcast_rss_url,
                apple_podcast_id=settings.podcast_apple_podcast_id,
            )
        ),
        normalize_service=NormalizeService(),
        episode_verifier=EpisodeVerifierService(
            provider=settings.verifier_provider,
            perplexity_client=PerplexityClient(
                api_key=settings.perplexity_api_key,
                model=settings.perplexity_model,
            ),
            gemini_client=GeminiClient(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
            ),
        ),
        state_store=StateStore(settings.state_file_path),
        slack_notifier=notifier,
        notify_score_threshold=settings.notify_score_threshold,
        verifier_model_name=_resolve_verifier_model_name(
            provider=provider,
            gemini_model=settings.gemini_model,
            perplexity_model=settings.perplexity_model,
        ),
    )


def _resolve_verifier_model_name(provider: str, gemini_model: str, perplexity_model: str) -> str:
    """Return the active model name for user-facing reporting."""

    if provider == "perplexity":
        return perplexity_model
    return gemini_model
