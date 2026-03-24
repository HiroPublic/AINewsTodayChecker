"""Utility script to preview sample episode data."""

import logging
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.clients.podcast_client import PodcastClient


def main() -> None:
    """Print sample episode metadata for quick inspection."""

    episode = PodcastClient().fetch_latest_episode()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("title=%s", episode.title)
    logging.info("summary=%s", episode.summary_text)


if __name__ == "__main__":
    main()
