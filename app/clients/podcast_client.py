"""Podcast episode source client."""

from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
import logging
import re
import xml.etree.ElementTree as ET

import httpx
from bs4 import BeautifulSoup


LOGGER = logging.getLogger(__name__)
EPISODE_NUMBER_PATTERN = re.compile(r"#(\d+)")
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"


@dataclass(slots=True)
class RawEpisode:
    """Raw episode payload from source."""

    source: str
    external_id: str
    episode_number: int | None
    title: str
    published_at: datetime
    episode_url: str
    summary_text: str
    transcript_text: str | None = None


class PodcastClient:
    """RSS-backed podcast client."""

    def __init__(self, rss_url: str = "", apple_podcast_id: str = "", timeout: float = 15.0) -> None:
        self._rss_url = rss_url
        self._apple_podcast_id = apple_podcast_id
        self._timeout = timeout

    def fetch_latest_episode(self) -> RawEpisode:
        """Fetch the latest episode from RSS."""

        episodes = self._fetch_episode_catalog()
        latest_episode_number = max(episodes)
        return episodes[latest_episode_number]

    def fetch_episode_by_number(self, episode_number: int | None = None) -> RawEpisode:
        """Fetch a specific episode by number from RSS."""

        episodes = self._fetch_episode_catalog()
        resolved_episode_number = episode_number or max(episodes)
        if resolved_episode_number not in episodes:
            available_range = f"1 to {max(episodes)}"
            raise ValueError(
                f"episode_number {resolved_episode_number} was not found in fetched data; available range is {available_range}"
            )
        return episodes[resolved_episode_number]

    def _fetch_episode_catalog(self) -> dict[int, RawEpisode]:
        """Fetch and parse the RSS feed into a catalog keyed by episode number."""

        rss_text = self._fetch_rss_text()
        return self._parse_rss(rss_text)

    def _fetch_rss_text(self) -> str:
        """Download RSS XML."""

        errors: list[str] = []
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            for rss_url in self._candidate_rss_urls(client):
                LOGGER.info("Fetching podcast RSS feed from %s", rss_url)
                try:
                    response = client.get(rss_url)
                    response.raise_for_status()
                    return response.text
                except httpx.HTTPError as exc:
                    LOGGER.warning("Failed to fetch podcast RSS feed from %s: %s", rss_url, exc)
                    errors.append(f"{rss_url}: {exc}")
        joined = " | ".join(errors) if errors else "no RSS URL candidates available"
        raise RuntimeError(
            "Unable to fetch podcast RSS feed. "
            f"Checked configured/feed-discovered URLs: {joined}. "
            "Verify PODCAST_RSS_URL, DNS/network access, and whether the feed URL is reachable from this environment."
        )

    def _candidate_rss_urls(self, client: httpx.Client) -> list[str]:
        """Build RSS URL candidates from config and Apple lookup."""

        urls: list[str] = []
        if self._rss_url:
            urls.append(self._rss_url)
        resolved_from_apple = self._resolve_rss_url_from_apple(client)
        if resolved_from_apple and resolved_from_apple not in urls:
            urls.append(resolved_from_apple)
        return urls

    def _resolve_rss_url_from_apple(self, client: httpx.Client) -> str | None:
        """Resolve the feed URL via Apple's public lookup API."""

        if not self._apple_podcast_id:
            return None
        LOGGER.info("Resolving podcast RSS URL from Apple Podcasts lookup API for id=%s", self._apple_podcast_id)
        try:
            response = client.get(ITUNES_LOOKUP_URL, params={"id": self._apple_podcast_id, "entity": "podcast"})
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            LOGGER.warning("Failed to resolve RSS URL from Apple Podcasts lookup API: %s", exc)
            return None
        results = data.get("results", [])
        for result in results:
            feed_url = result.get("feedUrl")
            if isinstance(feed_url, str) and feed_url:
                return feed_url
        return None

    def _parse_rss(self, rss_text: str) -> dict[int, RawEpisode]:
        """Parse RSS XML into an episode catalog."""

        root = ET.fromstring(rss_text)
        items = root.findall(".//item")
        episodes: dict[int, RawEpisode] = {}
        for item in items:
            episode = self._parse_item(item)
            if episode.episode_number is None:
                LOGGER.warning("Skipping RSS item without episode number: %s", episode.title)
                continue
            episodes[episode.episode_number] = episode
        if not episodes:
            raise ValueError("No episode with a parseable episode number was found in fetched RSS data")
        return episodes

    def _parse_item(self, item: ET.Element) -> RawEpisode:
        """Parse a single RSS item."""

        title = _get_child_text(item, "title") or "Untitled episode"
        guid = _get_child_text(item, "guid") or title
        link = _get_child_text(item, "link") or guid
        pub_date_text = _get_child_text(item, "pubDate") or ""
        description_html = _get_child_text(item, "description") or ""
        return RawEpisode(
            source="rss",
            external_id=guid,
            episode_number=_extract_episode_number(title),
            title=title,
            published_at=_parse_pub_date(pub_date_text),
            episode_url=link,
            summary_text=_html_to_text(description_html),
            transcript_text=None,
        )


def _extract_episode_number(title: str) -> int | None:
    """Extract an episode number from the title."""

    match = EPISODE_NUMBER_PATTERN.search(title)
    if not match:
        return None
    return int(match.group(1))


def _get_child_text(item: ET.Element, tag_name: str) -> str | None:
    """Return stripped child text for a simple RSS tag."""

    child = item.find(tag_name)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _html_to_text(value: str) -> str:
    """Convert RSS HTML descriptions into plain text."""

    if not value:
        return ""
    soup = BeautifulSoup(value, "html.parser")
    return soup.get_text("\n", strip=True)


def _parse_pub_date(value: str) -> datetime:
    """Parse pubDate into a timezone-aware datetime."""

    if not value:
        return datetime.now(tz=UTC)
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
