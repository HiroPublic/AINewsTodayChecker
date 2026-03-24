"""CLI entry point for GitHub Actions daily execution."""

import argparse
import logging
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.clients.podcast_client import PodcastClient
from app.clients.slack_client import SlackClient
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.notifier.slack import SlackNotifier
from app.persistence.state_store import StateStore
from app.services.fetch_service import FetchService
from app.services.job_service import JobService
from app.services.normalize_service import NormalizeService


LOGGER = logging.getLogger(__name__)


def build_job_service() -> JobService:
    """Build the daily job service from settings."""

    settings = get_settings()
    notifier = None
    if settings.slack_webhook_url:
        notifier = SlackNotifier(client=SlackClient(webhook_url=settings.slack_webhook_url))
    return JobService(
        fetch_service=FetchService(
            PodcastClient(
                rss_url=settings.podcast_rss_url,
                apple_podcast_id=settings.podcast_apple_podcast_id,
            )
        ),
        normalize_service=NormalizeService(),
        state_store=StateStore(settings.state_file_path),
        slack_notifier=notifier,
        notify_score_threshold=settings.notify_score_threshold,
    )


def main() -> int:
    """Execute the daily run and convert outcomes into exit codes."""

    parser = argparse.ArgumentParser(description="Run or preview the daily AI news verification job.")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Generate Slack notification messages without sending them or updating state.",
    )
    parser.add_argument(
        "--episode-number",
        type=int,
        default=None,
        help="Target a specific episode number when used with preview mode.",
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)
    LOGGER.info("Starting daily AI news verification job")
    if args.episode_number is not None and not args.preview:
        LOGGER.error("--episode-number can only be used together with --preview")
        return 1
    try:
        result = build_job_service().run_daily(preview_only=args.preview, episode_number=args.episode_number)
    except Exception:
        LOGGER.exception("Daily job failed")
        return 1

    LOGGER.info("Daily job finished with status=%s detail=%s", result.status, result.detail)
    if args.preview and result.preview_messages:
        for index, message in enumerate(result.preview_messages, start=1):
            LOGGER.info("Preview message %s\n%s", index, message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
