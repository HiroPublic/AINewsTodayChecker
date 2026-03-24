"""Database session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings


def build_session_factory(settings: Settings) -> sessionmaker:
    """Create a SQLAlchemy sessionmaker."""

    engine = create_engine(settings.database_url, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
