"""Claim parsing utilities."""

import re
from datetime import date

from app.schemas.claim import Claim, ParsedClaim


DATE_PATTERN = re.compile(r"(\d{1,2})月(\d{1,2})日")


def parse_claim(claim: Claim) -> ParsedClaim:
    """Perform light structured parsing on a raw claim."""

    text = claim.raw_text
    subject, predicate, object_text = _split_text(text)
    event_date = _extract_event_date(text)
    category = _detect_category(text)
    qualifiers = [token for token in ("完全統合", "正式発表", "世界初", "専用") if token in text]
    payload = claim.model_dump()
    payload.update(
        {
            "subject": subject,
            "predicate": predicate,
            "object_text": object_text,
            "qualifiers": qualifiers,
            "event_date": event_date,
            "category": category,
        }
    )
    return ParsedClaim(
        **payload,
    )


def _split_text(text: str) -> tuple[str | None, str | None, str | None]:
    parts = re.split(r"[、,]", text, maxsplit=1)
    if len(parts) == 1:
        return None, None, text
    subject = parts[0].strip()
    remainder = parts[1].strip()
    verb_match = re.search(r"(発表|公開|搭載)", remainder)
    if not verb_match:
        return subject, None, remainder
    idx = verb_match.start()
    return subject, remainder[idx : verb_match.end()], remainder[:idx].strip()


def _extract_event_date(text: str) -> date | None:
    match = DATE_PATTERN.search(text)
    if not match:
        return None
    month, day = map(int, match.groups())
    return date(2026, month, day)


def _detect_category(text: str) -> str:
    lowered = text.lower()
    if "gpu" in lowered or "nvidia" in lowered:
        return "hardware"
    if "gpt" in lowered or "claude" in lowered or "llm" in lowered:
        return "model"
    if "afeela" in lowered or "ソニー・ホンダ" in text:
        return "mobility"
    return "general"
