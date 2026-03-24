"""Scoring tests."""

from app.schemas.claim import ParsedClaim
from app.schemas.verdict import ClaimVerdict, VerdictLabel
from app.services.scoring_service import calculate_overall_score


def test_calculate_overall_score_rounds_mean() -> None:
    verdicts = [
        ClaimVerdict(claim=ParsedClaim(raw_text="a", order_index=1), label=VerdictLabel.TRUE, score=80, reason=""),
        ClaimVerdict(claim=ParsedClaim(raw_text="b", order_index=2), label=VerdictLabel.FALSE, score=20, reason=""),
    ]
    assert calculate_overall_score(verdicts) == 50
