"""Build Slack notification messages."""

from collections import Counter
import re

from app.schemas.episode import Episode
from app.schemas.verdict import ClaimVerdict, VerdictLabel
from app.utils.text import truncate_text


MAX_MESSAGE_LENGTH = 900


def build_report_messages(
    episode: Episode,
    verdicts: list[ClaimVerdict],
    overall_score: int,
) -> list[str]:
    """Build up to three Slack messages from verification results."""

    counts = Counter(verdict.label for verdict in verdicts)
    danger = _build_danger_level(overall_score, counts)
    display_title = _build_display_title(episode)
    episode_heading = f"エピソード: {display_title}"
    message_1 = "\n".join(
        [
            f"AI News Verifier",
            episode_heading,
            f"総合スコア: {overall_score}",
            f"*誤り*: {counts[VerdictLabel.FALSE]} / *誤解を招く*: {counts[VerdictLabel.MISLEADING]} / *未確認*: {counts[VerdictLabel.UNCONFIRMED]}",
            f"危険度: {danger}",
        ]
    )
    details = [
        f"{index}. *{_display_label(verdict)}* ({verdict.score}) {truncate_text(verdict.claim.raw_text, 120)}"
        for index, verdict in enumerate(verdicts, start=1)
    ]
    message_2 = "項目別結果\n" + "\n".join(details)
    reasons = [
        f"{index}. {truncate_text(verdict.reason, 120)}"
        for index, verdict in enumerate(verdicts, start=1)
    ]
    message_3 = "根拠と注意点\n" + "\n".join(reasons)
    return [truncate_text(message, MAX_MESSAGE_LENGTH) for message in (message_1, message_2, message_3)]


def should_notify(verdicts: list[ClaimVerdict], overall_score: int, threshold: int) -> bool:
    """Evaluate whether a notification should be sent."""

    counts = Counter(verdict.label for verdict in verdicts)
    return (
        overall_score < threshold
        or counts[VerdictLabel.FALSE] >= 1
        or (counts[VerdictLabel.MISLEADING] + counts[VerdictLabel.UNCONFIRMED]) >= 2
    )


def _build_danger_level(counts_score: int, counts: Counter) -> str:
    if counts[VerdictLabel.FALSE] >= 1 or counts_score < 50:
        return "高"
    if counts[VerdictLabel.MISLEADING] >= 1 or counts_score < 70:
        return "中"
    return "低"


def _build_display_title(episode: Episode) -> str:
    """Avoid repeating the episode number when the title already includes it."""

    if not episode.episode_number:
        return episode.title

    title_without_number = re.sub(
        rf"^\s*#\s*{episode.episode_number}\s*[:：\-–—]?\s*",
        "",
        episode.title,
    ).strip()
    if not title_without_number:
        return f"#{episode.episode_number}"
    return f"#{episode.episode_number} {title_without_number}"


def _display_label(verdict: ClaimVerdict) -> str:
    if verdict.display_label_ja:
        return verdict.display_label_ja
    defaults = {
        VerdictLabel.TRUE: "正確",
        VerdictLabel.MOSTLY_TRUE: "概ね正確",
        VerdictLabel.UNCONFIRMED: "未確認",
        VerdictLabel.MISLEADING: "誤解を招く",
        VerdictLabel.FALSE: "誤り",
    }
    return defaults[verdict.label]
