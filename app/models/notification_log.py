"""Notification log persistence model."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationLogModel(Base):
    """Notification log ORM model."""

    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(50))
    destination: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    message_preview: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
