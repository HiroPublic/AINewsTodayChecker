"""Claim persistence model."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClaimModel(Base):
    """Claim ORM model for future storage."""

    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"))
    raw_text: Mapped[str] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    predicate: Mapped[str | None] = mapped_column(String(255), nullable=True)
    object_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualifiers: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer)
