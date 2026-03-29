"""CLI wiring tests for the daily runner."""

from app.clients.gemini_client import GeminiClient
from app.clients.perplexity_client import PerplexityClient
from app.core.config import get_settings
from scripts.run_daily import build_job_service


def test_build_job_service_uses_configured_provider_by_default() -> None:
    get_settings.cache_clear()
    service = build_job_service()

    verifier = service._episode_verifier

    assert verifier.provider == "gemini"
    assert isinstance(verifier.perplexity_client, PerplexityClient)
    assert isinstance(verifier.gemini_client, GeminiClient)


def test_build_job_service_allows_provider_override() -> None:
    get_settings.cache_clear()
    service = build_job_service(provider="gemini")

    assert service._episode_verifier.provider == "gemini"
