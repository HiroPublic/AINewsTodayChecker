"""End-to-end daily job service."""

import logging
from dataclasses import dataclass

from app.notifier.slack import SlackNotifier
from app.persistence.state_store import RunState, StateStore
from app.schemas.episode import Episode
from app.services.claim_extractor import extract_claims
from app.services.claim_parser import parse_claim
from app.services.fetch_service import FetchService
from app.services.normalize_service import NormalizeService
from app.services.report_builder import build_report_messages
from app.services.scoring_service import calculate_overall_score
from app.services.verifier_service import verify_claim


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class DailyRunResult:
    """Daily job outcome model."""

    status: str
    detail: str
    notified: bool
    episode: Episode | None = None
    state: RunState | None = None
    preview_messages: list[str] | None = None


class JobService:
    """Run the fetch, analyze, and notify workflow."""

    def __init__(
        self,
        fetch_service: FetchService,
        normalize_service: NormalizeService,
        state_store: StateStore,
        slack_notifier: SlackNotifier | None,
        notify_score_threshold: int,
    ) -> None:
        self._fetch_service = fetch_service
        self._normalize_service = normalize_service
        self._state_store = state_store
        self._slack_notifier = slack_notifier
        self._notify_score_threshold = notify_score_threshold

    def run_daily(self, preview_only: bool = False, episode_number: int | None = None) -> DailyRunResult:
        """Execute the full daily verification job."""

        current_state = self._state_store.load()
        raw_episode = self._fetch_service.fetch_latest(episode_number=episode_number)
        episode = self._normalize_service.normalize(raw_episode)
        if not preview_only and current_state.last_episode_hash == episode.content_hash:
            LOGGER.info("Duplicate episode detected; skipping notification")
            return DailyRunResult(status="skipped", detail="duplicate episode hash", notified=False, episode=episode)

        claims = [parse_claim(claim) for claim in extract_claims(episode.summary_text)]
        verdicts = [verify_claim(claim) for claim in claims]
        overall_score = calculate_overall_score(verdicts)
        messages = build_report_messages(episode, verdicts, overall_score)
        if preview_only:
            LOGGER.info("Preview mode enabled; skipping Slack send and state update")
            return DailyRunResult(
                status="preview",
                detail="preview generated",
                notified=False,
                episode=episode,
                preview_messages=messages,
            )

        if self._slack_notifier is None:
            raise RuntimeError("Slack notifier is not configured")

        self._slack_notifier.notify_messages(messages)
        updated_state = self._state_store.save_success(episode.content_hash, episode.title)
        return DailyRunResult(
            status="notified",
            detail="notification sent",
            notified=True,
            episode=episode,
            state=updated_state,
            preview_messages=messages,
        )
