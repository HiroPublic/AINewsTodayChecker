"""Episode normalization service."""

from app.clients.podcast_client import RawEpisode
from app.schemas.episode import Episode
from app.utils.hashes import build_content_hash


class NormalizeService:
    """Normalize raw source payloads into internal episode schema."""

    def normalize(self, raw_episode: RawEpisode) -> Episode:
        """Normalize a raw episode and compute content hash."""

        content_hash = build_content_hash(
            raw_episode.source,
            raw_episode.external_id,
            raw_episode.title,
            raw_episode.summary_text,
            raw_episode.transcript_text or "",
        )
        return Episode(
            source=raw_episode.source,
            external_id=raw_episode.external_id,
            episode_number=raw_episode.episode_number,
            title=raw_episode.title,
            published_at=raw_episode.published_at,
            episode_url=raw_episode.episode_url,
            summary_text=raw_episode.summary_text,
            transcript_text=raw_episode.transcript_text,
            content_hash=content_hash,
        )
