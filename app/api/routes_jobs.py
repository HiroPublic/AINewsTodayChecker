"""Minimal job routes for the MVP."""

from fastapi import APIRouter, Depends, Query
from fastapi import HTTPException

from app.api.deps import get_job_service
from app.schemas.job import JobResult
from app.services.job_service import JobService


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/run-daily", response_model=JobResult)
def run_daily(job_service: JobService = Depends(get_job_service)) -> JobResult:
    """Run the daily verification job."""

    result = job_service.run_daily()
    return JobResult(
        status=result.status,
        detail=result.detail,
        notified=result.notified,
        preview_messages=result.preview_messages or [],
    )


@router.post("/preview-latest", response_model=JobResult)
def preview_latest(
    episode_number: int | None = Query(default=None, ge=1),
    job_service: JobService = Depends(get_job_service),
) -> JobResult:
    """Generate Slack messages without sending them."""

    try:
        result = job_service.run_daily(preview_only=True, episode_number=episode_number)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JobResult(
        status=result.status,
        detail=result.detail,
        notified=result.notified,
        preview_messages=result.preview_messages or [],
    )


@router.post("/fetch-latest", response_model=JobResult)
def fetch_latest() -> JobResult:
    """Placeholder route for future workflow step separation."""

    return JobResult(status="not_implemented", detail="Use /jobs/run-daily for MVP.")


@router.post("/analyze-latest", response_model=JobResult)
def analyze_latest() -> JobResult:
    """Placeholder route for future workflow step separation."""

    return JobResult(status="not_implemented", detail="Use /jobs/run-daily for MVP.")


@router.post("/notify-latest", response_model=JobResult)
def notify_latest() -> JobResult:
    """Placeholder route for future workflow step separation."""

    return JobResult(status="not_implemented", detail="Use /jobs/run-daily for MVP.")
