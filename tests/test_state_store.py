"""State store tests."""

from pathlib import Path

from app.persistence.state_store import StateStore


def test_state_store_loads_empty_then_saves(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "last_run.json")
    empty = store.load()
    assert empty.last_episode_hash is None

    saved = store.save_success("hash", "title")
    reloaded = store.load()
    assert saved.last_episode_hash == "hash"
    assert reloaded.last_title == "title"
