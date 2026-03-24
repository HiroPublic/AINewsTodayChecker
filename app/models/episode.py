"""Episode persistence model."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EpisodeModel(Base):
    """Episode ORM model kept as a future persistence seam."""

    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(500))
    episode_url: Mapped[str] = mapped_column(String(1000))
    summary_text: Mapped[str] = mapped_column(Text)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
