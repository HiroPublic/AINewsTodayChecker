"""Episode application service."""

from app.schemas.episode import Episode


class EpisodeService:
    """In-memory episode holder for MVP endpoints."""

    def __init__(self) -> None:
        self._latest_episode: Episode | None = None

    def set_latest(self, episode: Episode) -> None:
        """Store the latest episode in memory."""

        self._latest_episode = episode

    def get_latest(self) -> Episode | None:
        """Return latest episode if available."""

        return self._latest_episode
