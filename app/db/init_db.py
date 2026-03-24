"""Database initialization entry points."""

from app.db.base import Base


def init_db(engine) -> None:
    """Create tables for future persistence use."""

    Base.metadata.create_all(bind=engine)
