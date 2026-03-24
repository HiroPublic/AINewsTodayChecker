"""Hash helpers."""

import hashlib


def build_content_hash(*parts: str) -> str:
    """Create a stable hash across source content fields."""

    normalized = "||".join(parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
