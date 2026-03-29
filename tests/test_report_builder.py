"""Report builder tests."""

from datetime import UTC, datetime

from app.schemas.claim import ParsedClaim
from app.schemas.episode import Episode
from app.schemas.verdict import ClaimVerdict, VerdictLabel
from app.services.report_builder import build_report_messages, should_notify


def test_build_report_messages_returns_three_messages() -> None:
    episode = Episode(
        source="sample",
        external_id="id",
        episode_number=98,
        title="title",
        published_at=datetime(2026, 3, 24, tzinfo=UTC),
        episode_url="https://example.com",
        summary_text="summary",
        content_hash="hash",
    )
    verdicts = [
        ClaimVerdict(
            claim=ParsedClaim(raw_text="raw", order_index=1),
            label=VerdictLabel.FALSE,
            display_label_ja="誤り",
            score=10,
            reason="reason",
        )
    ]
    messages = build_report_messages(episode, verdicts, overall_score=10, verifier_model_name="gemini-2.5-flash")
    assert len(messages) == 3
    assert messages[0].startswith("AI News Verifier (gemini-2.5-flash)")
    assert "#98" in messages[0]
    assert "*誤り*: 1 / *誤解を招く*: 0 / *未確認*: 0" in messages[0]
    assert "1. *誤り* (10) raw" in messages[1]
    assert should_notify(verdicts, overall_score=10, threshold=60) is True


def test_build_report_messages_does_not_repeat_episode_number_in_title() -> None:
    episode = Episode(
        source="sample",
        external_id="id",
        episode_number=98,
        title="#98 最新AI情報 AIニューストゥデイ 2026-03-24",
        published_at=datetime(2026, 3, 24, tzinfo=UTC),
        episode_url="https://example.com",
        summary_text="summary",
        content_hash="hash",
    )
    verdicts = [
        ClaimVerdict(
            claim=ParsedClaim(raw_text="raw", order_index=1),
            label=VerdictLabel.FALSE,
            display_label_ja="誤り",
            score=10,
            reason="reason",
        )
    ]

    messages = build_report_messages(episode, verdicts, overall_score=10)

    assert "エピソード: #98 最新AI情報 AIニューストゥデイ 2026-03-24" in messages[0]
    assert "#98 #98" not in messages[0]
