"""Episode verification services."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from app.clients.perplexity_client import PerplexityClient
from app.schemas.claim import Claim
from app.schemas.episode import Episode
from app.schemas.verdict import ClaimVerdict, VerdictLabel
from app.services.claim_extractor import extract_claims
from app.services.claim_parser import parse_claim


LOGGER = logging.getLogger(__name__)

MISLEADING_TERMS = ("完全統合", "専用", "正式発表", "世界初", "次世代GPU")
FALSE_TERMS = ("1000万トークン", "50兆トークン")

SYSTEM_PROMPT = """You are a conservative fact-checking assistant for AI and tech news.

Verify the article using available evidence and return strict JSON only.

Rules:
- Be conservative. If evidence is weak, prefer UNCONFIRMED.
- Penalize exaggeration, weak sourcing, unrealistic numbers, rumor-as-fact wording, and date inconsistencies.
- Prefer primary and official sources.
- Extract 3 to 7 key factual claims.
- Keep claim_reason under 220 characters.
- Keep overall_summary under 320 characters.
- Use score ranges consistently by label:
  - TRUE: 85-100
  - MOSTLY_TRUE: 70-84
  - UNCONFIRMED: 45-69
  - MISLEADING: 20-44
  - FALSE: 0-19
- UNCONFIRMED should not default to zero just because evidence is missing.
- Never output prose outside JSON.
"""

USER_PROMPT_TEMPLATE = """Evaluate the following article.

Return exactly:
{{
  "overall_score": 0,
  "overall_verdict": "",
  "needs_attention": true,
  "overall_summary": "",
  "claims": [
    {{
      "claim_text": "",
      "label": "",
      "score": 0,
      "claim_reason": "",
      "risk_flags": [],
      "evidence": [
        {{
          "title": "",
          "url": "",
          "source_type": "primary"
        }}
      ]
    }}
  ]
}}

Allowed labels:
- TRUE
- MOSTLY_TRUE
- UNCONFIRMED
- MISLEADING
- FALSE

Article title:
{title}

Article URL:
{url}

Article text:
{text}
"""


class EvidenceItem(BaseModel):
    """Evidence item returned by Perplexity."""

    title: str = ""
    url: str = ""
    source_type: str = "unknown"


class EvaluatedClaim(BaseModel):
    """Claim evaluation payload returned by Perplexity."""

    claim_text: str
    label: VerdictLabel
    score: int
    claim_reason: str
    risk_flags: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class ArticleEvaluation(BaseModel):
    """Full article evaluation payload returned by Perplexity."""

    overall_score: int
    overall_verdict: VerdictLabel
    needs_attention: bool
    overall_summary: str
    claims: list[EvaluatedClaim]


@dataclass(slots=True)
class EpisodeVerifierService:
    """Verify episodes using Perplexity with rule-based fallback."""

    perplexity_client: PerplexityClient | None = None
    artifacts_dir: Path = Path("artifacts")

    def verify_episode(self, episode: Episode) -> list[ClaimVerdict]:
        """Verify an episode and return claim-level verdicts."""

        if self.perplexity_client and self.perplexity_client.is_configured():
            try:
                return self._verify_with_perplexity(episode)
            except Exception:
                LOGGER.exception("Perplexity verification failed; falling back to rule-based verification")
        return self._verify_rule_based(episode)

    def _verify_with_perplexity(self, episode: Episode) -> list[ClaimVerdict]:
        user_prompt = USER_PROMPT_TEMPLATE.format(
            title=episode.title,
            url=episode.episode_url,
            text=episode.summary_text,
        )
        self._write_json_artifact(
            "prompt.json",
            {
                "system_prompt": SYSTEM_PROMPT,
                "user_prompt": user_prompt,
                "episode_title": episode.title,
                "episode_url": episode.episode_url,
            },
        )
        try:
            payload = self.perplexity_client.evaluate_article(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
        except Exception as exc:
            self._write_json_artifact(
                "perplexity-response.json",
                {
                    "ok": False,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            raise
        self._write_json_artifact(
            "perplexity-response.json",
            _build_response_artifact(payload),
        )
        evaluation = _parse_article_evaluation(payload)
        verdicts: list[ClaimVerdict] = []
        for index, evaluated_claim in enumerate(evaluation.claims, start=1):
            parsed_claim = parse_claim(Claim(raw_text=evaluated_claim.claim_text, order_index=index))
            verdicts.append(
                ClaimVerdict(
                    claim=parsed_claim,
                    label=evaluated_claim.label,
                    score=_normalize_score(evaluated_claim.label, evaluated_claim.score),
                    reason=evaluated_claim.claim_reason,
                )
            )
        if verdicts:
            return verdicts
        raise RuntimeError("Perplexity returned no claims to evaluate")

    def _verify_rule_based(self, episode: Episode) -> list[ClaimVerdict]:
        claims = [parse_claim(claim) for claim in extract_claims(episode.summary_text)]
        return [verify_claim(claim) for claim in claims]

    def _write_json_artifact(self, filename: str, payload: dict[str, object]) -> None:
        """Persist debug artifacts for prompt and Perplexity responses."""

        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        path = self.artifacts_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def verify_claim(claim) -> ClaimVerdict:
    """Verify a claim using deterministic fallback rules."""

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


def _parse_article_evaluation(payload: str) -> ArticleEvaluation:
    """Extract a validated evaluation object from a model response."""

    try:
        return ArticleEvaluation.model_validate_json(payload)
    except ValidationError:
        start = payload.find("{")
        end = payload.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        candidate = payload[start : end + 1]
        normalized = json.dumps(json.loads(candidate), ensure_ascii=False)
        return ArticleEvaluation.model_validate_json(normalized)


def _build_response_artifact(payload: str) -> dict[str, object]:
    """Build a readable artifact from the raw model response."""

    artifact: dict[str, object] = {
        "ok": True,
        "raw_response": payload,
    }
    try:
        artifact["parsed_response"] = json.loads(payload)
        return artifact
    except json.JSONDecodeError:
        start = payload.find("{")
        end = payload.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return artifact
        candidate = payload[start : end + 1]
        try:
            artifact["parsed_response"] = json.loads(candidate)
        except json.JSONDecodeError:
            return artifact
    return artifact


def _normalize_score(label: VerdictLabel, score: int) -> int:
    """Clamp model scores into stable label-specific ranges."""

    bounded = max(0, min(100, score))
    ranges = {
        VerdictLabel.TRUE: (85, 100),
        VerdictLabel.MOSTLY_TRUE: (70, 84),
        VerdictLabel.UNCONFIRMED: (45, 69),
        VerdictLabel.MISLEADING: (20, 44),
        VerdictLabel.FALSE: (0, 19),
    }
    low, high = ranges[label]
    if low <= bounded <= high:
        return bounded
    # Preserve relative intent when possible, but keep the score inside the label band.
    return max(low, min(high, bounded if bounded != 0 else low))
