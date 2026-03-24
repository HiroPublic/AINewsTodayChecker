"""Episode schemas."""

from datetime import datetime

from pydantic import BaseModel


class Episode(BaseModel):
    """Normalized episode data model."""

    source: str
    external_id: str
    episode_number: int | None = None
    title: str
    published_at: datetime
    episode_url: str
    summary_text: str
    transcript_text: str | None = None
    content_hash: str


class EpisodeView(Episode):
    """Episode response model."""

    id: str
