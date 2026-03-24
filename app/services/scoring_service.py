"""Scoring utilities."""

from statistics import mean

from app.schemas.verdict import ClaimVerdict


def calculate_overall_score(verdicts: list[ClaimVerdict]) -> int:
    """Calculate an integer average score for episode-level reporting."""

    if not verdicts:
        return 0
    return round(mean(verdict.score for verdict in verdicts))
