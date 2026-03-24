"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes_episodes import router as episodes_router
from app.api.routes_jobs import router as jobs_router
from app.core.config import get_settings
from app.core.logging import configure_logging


settings = get_settings()
configure_logging(settings)

app = FastAPI(title=settings.app_name)
app.include_router(jobs_router)
app.include_router(episodes_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return application health."""

    return {"status": "ok", "app": settings.app_name}
