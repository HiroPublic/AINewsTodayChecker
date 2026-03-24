"""Episode fetching orchestration."""

from app.clients.podcast_client import PodcastClient, RawEpisode


class FetchService:
    """Facade over external episode source clients."""

    def __init__(self, podcast_client: PodcastClient) -> None:
        self._podcast_client = podcast_client

    def fetch_latest(self, episode_number: int | None = None) -> RawEpisode:
        """Fetch the latest episode or a requested episode number for preview/debug."""

        if episode_number is None:
            return self._podcast_client.fetch_latest_episode()
        return self._podcast_client.fetch_episode_by_number(episode_number)
