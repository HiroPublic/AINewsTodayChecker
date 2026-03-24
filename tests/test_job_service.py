"""Job service end-to-end behavior tests."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.clients.podcast_client import RawEpisode
from app.persistence.state_store import StateStore
from app.services.job_service import JobService
from app.services.normalize_service import NormalizeService


class FakeSlackNotifier:
    """Collect sent messages without external I/O."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify_messages(self, messages: list[str]) -> None:
        self.messages.extend(messages)


class FakeFetchService:
    """Return deterministic episodes without network access."""

    def fetch_latest(self, episode_number: int | None = None) -> RawEpisode:
        resolved_number = episode_number or 98
        if resolved_number != 98:
            raise ValueError(f"episode_number {resolved_number} was not found in fetched data; available range is 1 to 98")
        return RawEpisode(
            source="rss",
            external_id=f"ep-{resolved_number}",
            episode_number=resolved_number,
            title="最新AI情報 AIニューストゥデイ 2026-03-24",
            published_at=datetime(2026, 3, 24, 6, 20, tzinfo=UTC),
            episode_url=f"https://example.com/{resolved_number}",
            summary_text="""3月24日のAIニュースをお届けします。
• アップル、SiriにGPT-5を完全統合と発表（3月23日）
• ソニー・ホンダ、AFEELAに感情推論AI搭載（3月23日）
• Anthropic、1000万トークン対応のClaude 4公開（3月22日）
• サイバーエージェント、日本語特化の50兆トークンLLM公開（3月23日）
• NVIDIA、GPT-5専用の次世代GPU「Blackwell Ultra」発表（3月23日）""",
            transcript_text=None,
        )


def test_job_service_saves_state_after_notification(tmp_path: Path) -> None:
    notifier = FakeSlackNotifier()
    service = JobService(
        fetch_service=FakeFetchService(),
        normalize_service=NormalizeService(),
        state_store=StateStore(tmp_path / "last_run.json"),
        slack_notifier=notifier,
        notify_score_threshold=60,
    )

    result = service.run_daily()

    assert result.status == "notified"
    assert result.notified is True
    assert len(notifier.messages) == 3
    assert StateStore(tmp_path / "last_run.json").load().last_episode_hash is not None


def test_job_service_skips_duplicate_hash(tmp_path: Path) -> None:
    state_store = StateStore(tmp_path / "last_run.json")
    normalized = NormalizeService().normalize(FakeFetchService().fetch_latest())
    state_store.save_success(normalized.content_hash, normalized.title)
    notifier = FakeSlackNotifier()
    service = JobService(
        fetch_service=FakeFetchService(),
        normalize_service=NormalizeService(),
        state_store=state_store,
        slack_notifier=notifier,
        notify_score_threshold=60,
    )

    result = service.run_daily()

    assert result.status == "skipped"
    assert notifier.messages == []


def test_job_service_preview_does_not_send_or_save_state(tmp_path: Path) -> None:
    notifier = FakeSlackNotifier()
    state_path = tmp_path / "last_run.json"
    service = JobService(
        fetch_service=FakeFetchService(),
        normalize_service=NormalizeService(),
        state_store=StateStore(state_path),
        slack_notifier=notifier,
        notify_score_threshold=60,
    )

    result = service.run_daily(preview_only=True)

    assert result.status == "preview"
    assert result.preview_messages is not None
    assert len(result.preview_messages) == 3
    assert "#98" in result.preview_messages[0]
    assert notifier.messages == []
    assert state_path.exists() is False


def test_job_service_preview_can_target_episode_number(tmp_path: Path) -> None:
    service = JobService(
        fetch_service=FakeFetchService(),
        normalize_service=NormalizeService(),
        state_store=StateStore(tmp_path / "last_run.json"),
        slack_notifier=FakeSlackNotifier(),
        notify_score_threshold=60,
    )

    result = service.run_daily(preview_only=True, episode_number=98)

    assert result.episode is not None
    assert result.episode.episode_number == 98
    assert result.preview_messages is not None
    assert "#98" in result.preview_messages[0]


def test_job_service_preview_rejects_missing_episode_number(tmp_path: Path) -> None:
    service = JobService(
        fetch_service=FakeFetchService(),
        normalize_service=NormalizeService(),
        state_store=StateStore(tmp_path / "last_run.json"),
        slack_notifier=FakeSlackNotifier(),
        notify_score_threshold=60,
    )

    with pytest.raises(ValueError, match="episode_number 123 was not found in fetched data"):
        service.run_daily(preview_only=True, episode_number=123)
