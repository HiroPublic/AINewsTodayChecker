"""Verdict schemas."""

from enum import StrEnum

from pydantic import BaseModel

from app.schemas.claim import ParsedClaim


class VerdictLabel(StrEnum):
    """Supported verdict labels."""

    TRUE = "TRUE"
    MOSTLY_TRUE = "MOSTLY_TRUE"
    UNCONFIRMED = "UNCONFIRMED"
    MISLEADING = "MISLEADING"
    FALSE = "FALSE"


class ClaimVerdict(BaseModel):
    """Claim level verification result."""

    claim: ParsedClaim
    label: VerdictLabel
    display_label_ja: str = ""
    score: int
    reason: str


class EpisodeVerdict(BaseModel):
    """Episode level verification aggregate."""

    episode_id: str
    overall_score: int
    verdicts: list[ClaimVerdict]
