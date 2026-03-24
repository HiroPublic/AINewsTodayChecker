"""JSON-backed state store for duplicate notification prevention."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(slots=True)
class RunState:
    """Daily job state snapshot."""

    last_episode_hash: str | None = None
    last_title: str | None = None
    last_run_at: str | None = None
    last_status: str | None = None


class StateStore:
    """Store job state in a JSON file compatible with GitHub Actions cache."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> RunState:
        """Load state, returning an empty state when absent."""

        if not self._path.exists():
            return RunState()
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return RunState(**data)

    def save_success(self, episode_hash: str, title: str) -> RunState:
        """Persist state after a successful notification."""

        state = RunState(
            last_episode_hash=episode_hash,
            last_title=title,
            last_run_at=datetime.now(tz=UTC).isoformat(),
            last_status="success",
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
        return state
