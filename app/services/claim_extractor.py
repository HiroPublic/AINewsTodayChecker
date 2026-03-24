"""Claim extraction from summary text."""

from app.schemas.claim import Claim
from app.utils.text import split_summary_into_lines


def extract_claims(summary_text: str) -> list[Claim]:
    """Extract claims from bullet points or sentence-like summary fragments."""

    lines = split_summary_into_lines(summary_text)
    return [Claim(raw_text=line, order_index=index) for index, line in enumerate(lines, start=1)]
