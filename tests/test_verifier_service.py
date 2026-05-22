"""Verifier service tests."""

from datetime import UTC, datetime
import json

from app.schemas.episode import Episode
from app.schemas.verdict import VerdictLabel
from app.services.verifier_service import EpisodeVerifierService


class FakePerplexityClient:
    """Return deterministic JSON without external I/O."""

    def __init__(self, payload: str, configured: bool = True) -> None:
        self._payload = payload
        self._configured = configured

    def is_configured(self) -> bool:
        return self._configured

    def evaluate_article(self, system_prompt: str, user_prompt: str) -> str:
        return self._payload


class FakeGeminiClient(FakePerplexityClient):
    """Reuse the same deterministic stub for Gemini-backed tests."""


def build_episode() -> Episode:
    return Episode(
        source="rss",
        external_id="ep-98",
        episode_number=98,
        title="最新AI情報 AIニューストゥデイ 2026-03-24",
        published_at=datetime(2026, 3, 24, 6, 20, tzinfo=UTC),
        episode_url="https://example.com/98",
        summary_text="アップル、SiriにGPT-5を完全統合と発表（3月23日）",
        content_hash="hash",
    )


def test_verify_episode_uses_perplexity_response_when_configured(tmp_path) -> None:
    service = EpisodeVerifierService(
        provider="perplexity",
        perplexity_client=FakePerplexityClient(
            """{
                "overall_score": 41,
                "overall_verdict": "MISLEADING",
                "needs_attention": true,
                "overall_summary": "summary",
                "claims": [
                    {
                        "claim_text": "アップル、SiriにGPT-5を完全統合と発表（3月23日）",
                        "label": "MISLEADING",
                        "display_label_ja": "誤解を招く",
                        "score": 41,
                        "claim_reason": "根拠に対して表現が強すぎます。",
                        "risk_flags": ["exaggeration"],
                        "evidence": []
                    }
                ]
            }"""
        ),
        artifacts_dir=tmp_path,
    )

    verdicts = service.verify_episode(build_episode())

    assert len(verdicts) == 1
    assert verdicts[0].label == VerdictLabel.MISLEADING
    assert verdicts[0].display_label_ja == "誤解を招く"
    assert verdicts[0].score == 41
    prompt = json.loads((tmp_path / "prompt.json").read_text(encoding="utf-8"))
    response = json.loads((tmp_path / "perplexity-response.json").read_text(encoding="utf-8"))
    assert "system_prompt" in prompt
    assert "Return each `claim_text` in the original Japanese from the target article." in prompt["system_prompt"]
    assert "Judge stale-news status relative to the parenthesized date written at the end of each news item" in prompt["system_prompt"]
    assert "Use the explicit Date context in the user prompt" in prompt["system_prompt"]
    assert "older evidence only as stale-news evidence" in prompt["system_prompt"]
    assert "user_prompt" in prompt
    assert "display_label_ja" in prompt["user_prompt"]
    assert "Date context:" in prompt["user_prompt"]
    assert "Episode published date in Asia/Tokyo: 2026-03-24" in prompt["user_prompt"]
    assert "Reference year for yearless Japanese dates in this article: 2026" in prompt["user_prompt"]
    assert "Do not substitute 2024 or 2025 for yearless dates." in prompt["user_prompt"]
    assert "older evidence only to explain stale-news risk" in prompt["user_prompt"]
    assert prompt["episode_published_at"] == "2026-03-24T06:20:00+00:00"
    assert "Reference year for yearless Japanese dates in this article: 2026" in prompt["date_context"]
    assert response["ok"] is True
    assert "raw_response" in response
    assert response["parsed_response"]["claims"][0]["label"] == "MISLEADING"
    assert response["parsed_response"]["claims"][0]["display_label_ja"] == "誤解を招く"


def test_verify_episode_normalizes_zero_score_for_unconfirmed(tmp_path) -> None:
    service = EpisodeVerifierService(
        provider="perplexity",
        perplexity_client=FakePerplexityClient(
            """{
                "overall_score": 1,
                "overall_verdict": "UNCONFIRMED",
                "needs_attention": true,
                "overall_summary": "summary",
                "claims": [
                    {
                        "claim_text": "未確認の主張",
                        "label": "UNCONFIRMED",
                        "display_label_ja": "既報",
                        "score": 0,
                        "claim_reason": "確認できませんでした。",
                        "risk_flags": [],
                        "evidence": []
                    }
                ]
            }"""
        ),
        artifacts_dir=tmp_path,
    )

    verdicts = service.verify_episode(build_episode())

    assert verdicts[0].label == VerdictLabel.UNCONFIRMED
    assert verdicts[0].display_label_ja == "既報"
    assert verdicts[0].score == 45


def test_verify_episode_falls_back_to_rule_based_when_client_not_configured() -> None:
    service = EpisodeVerifierService(
        provider="perplexity",
        perplexity_client=FakePerplexityClient(payload="{}", configured=False)
    )

    verdicts = service.verify_episode(build_episode())

    assert len(verdicts) == 1
    assert verdicts[0].label == VerdictLabel.MISLEADING


def test_verify_episode_uses_gemini_when_provider_is_gemini(tmp_path) -> None:
    service = EpisodeVerifierService(
        provider="gemini",
        gemini_client=FakeGeminiClient(
            """{
                "overall_score": 88,
                "overall_verdict": "TRUE",
                "needs_attention": false,
                "overall_summary": "summary",
                "claims": [
                    {
                        "claim_text": "アップル、SiriにGPT-5を完全統合と発表（3月23日）",
                        "label": "TRUE",
                        "display_label_ja": "正確",
                        "score": 88,
                        "claim_reason": "十分な根拠があると判断しました。",
                        "risk_flags": [],
                        "evidence": []
                    }
                ]
            }"""
        ),
        artifacts_dir=tmp_path,
    )

    verdicts = service.verify_episode(build_episode())

    assert len(verdicts) == 1
    assert verdicts[0].label == VerdictLabel.TRUE
    response = json.loads((tmp_path / "gemini-response.json").read_text(encoding="utf-8"))
    assert response["ok"] is True
    assert response["parsed_response"]["claims"][0]["label"] == "TRUE"
