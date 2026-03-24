"""Claim extractor tests."""

from app.services.claim_extractor import extract_claims


def test_extract_claims_prefers_bullets() -> None:
    summary = "冒頭\n• 1件目\n• 2件目"
    claims = extract_claims(summary)
    assert [claim.raw_text for claim in claims] == ["1件目", "2件目"]
