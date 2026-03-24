"""Rule-based claim verification."""

from app.schemas.claim import ParsedClaim
from app.schemas.verdict import ClaimVerdict, VerdictLabel


MISLEADING_TERMS = ("完全統合", "専用", "正式発表", "世界初", "次世代GPU")
FALSE_TERMS = ("1000万トークン", "50兆トークン")


def verify_claim(claim: ParsedClaim) -> ClaimVerdict:
    """Verify a claim using deterministic MVP rules."""

    text = claim.raw_text
    if any(term in text for term in FALSE_TERMS):
        return ClaimVerdict(
            claim=claim,
            label=VerdictLabel.FALSE,
            score=15,
            reason="非現実的な数値表現が含まれており、初期ルールでは FALSE と判定しました。",
        )
    if any(term in text for term in MISLEADING_TERMS):
        return ClaimVerdict(
            claim=claim,
            label=VerdictLabel.MISLEADING,
            score=40,
            reason="強い断定表現または誇張の疑いがある語を含むため、MISLEADING 寄りと判定しました。",
        )
    if claim.subject and claim.object_text:
        return ClaimVerdict(
            claim=claim,
            label=VerdictLabel.MOSTLY_TRUE,
            score=72,
            reason="主体と出来事は読み取れる一方、裏取り根拠が不足しているため MOSTLY_TRUE としました。",
        )
    return ClaimVerdict(
        claim=claim,
        label=VerdictLabel.UNCONFIRMED,
        score=55,
        reason="情報が不足しており、初期ルールだけでは十分に検証できませんでした。",
    )
