"""Episode routes for lightweight inspection endpoints."""

from fastapi import APIRouter, HTTPException

from app.clients.podcast_client import PodcastClient
from app.core.config import get_settings
from app.schemas.episode import EpisodeView
from app.services.normalize_service import NormalizeService


router = APIRouter(prefix="/episodes", tags=["episodes"])


def _latest_episode_view() -> EpisodeView:
    settings = get_settings()
    episode = NormalizeService().normalize(
        PodcastClient(
            rss_url=settings.podcast_rss_url,
            apple_podcast_id=settings.podcast_apple_podcast_id,
        ).fetch_latest_episode()
    )
    return EpisodeView(id=episode.external_id, **episode.model_dump())


@router.get("/latest", response_model=EpisodeView)
def get_latest_episode() -> EpisodeView:
    """Return the latest normalized sample episode."""

    return _latest_episode_view()


@router.get("/{episode_id}", response_model=EpisodeView)
def get_episode(episode_id: str) -> EpisodeView:
    """Return the sample episode when IDs match."""

    episode = _latest_episode_view()
    if episode.id != episode_id:
        raise HTTPException(status_code=404, detail="episode not found")
    return episode
