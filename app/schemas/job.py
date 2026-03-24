"""Job request and response schemas."""

from pydantic import BaseModel, Field


class JobResult(BaseModel):
    """Basic job execution response."""

    status: str
    detail: str
    notified: bool = False
    preview_messages: list[str] = Field(default_factory=list)
