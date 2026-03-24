"""Claim schemas."""

from datetime import date

from pydantic import BaseModel, Field


class Claim(BaseModel):
    """Claim extracted from episode summary."""

    raw_text: str
    order_index: int
    subject: str | None = None
    predicate: str | None = None
    object_text: str | None = None
    qualifiers: list[str] = Field(default_factory=list)
    event_date: date | None = None
    category: str | None = None


class ParsedClaim(Claim):
    """Parsed claim with structure filled in."""
