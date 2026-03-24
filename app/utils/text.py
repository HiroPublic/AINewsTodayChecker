"""Text processing utilities."""

import re


BULLET_PREFIXES = ("•", "-", "*")


def split_summary_into_lines(summary_text: str) -> list[str]:
    """Split summary text into normalized candidate lines."""

    lines = [line.strip() for line in summary_text.splitlines() if line.strip()]
    items: list[str] = []
    for line in lines:
        if line.startswith(BULLET_PREFIXES):
            items.append(line.lstrip("•-* ").strip())
    if items:
        return items
    return [segment.strip() for segment in re.split(r"[。\n]+", summary_text) if segment.strip()]


def truncate_text(text: str, limit: int) -> str:
    """Truncate text without raising on short input."""

    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
