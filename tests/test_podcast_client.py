"""Podcast RSS client tests."""

from app.clients.podcast_client import PodcastClient


RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>最新AI情報 AIニューストゥデイ</title>
    <item>
      <title>#98 OpenAI新発表 | 最新AI情報 AIニューストゥデイ</title>
      <guid>ep-98</guid>
      <link>https://example.com/98</link>
      <pubDate>Mon, 24 Mar 2026 06:20:00 +0900</pubDate>
      <description><![CDATA[<p>3月24日のAIニュースをお届けします。</p><ul><li>ニュース1</li></ul>]]></description>
    </item>
    <item>
      <title>#97 前回 | 最新AI情報 AIニューストゥデイ</title>
      <guid>ep-97</guid>
      <link>https://example.com/97</link>
      <pubDate>Sun, 23 Mar 2026 06:20:00 +0900</pubDate>
      <description><![CDATA[<p>3月23日のAIニュースをお届けします。</p>]]></description>
    </item>
  </channel>
</rss>"""


class FakePodcastClient(PodcastClient):
    """Podcast client with fixed RSS data for tests."""

    def __init__(self) -> None:
        super().__init__(rss_url="https://example.com/feed.xml", apple_podcast_id="1728333812")

    def _fetch_rss_text(self) -> str:
        return RSS_SAMPLE


def test_fetch_latest_episode_uses_highest_episode_number() -> None:
    episode = FakePodcastClient().fetch_latest_episode()

    assert episode.episode_number == 98
    assert episode.external_id == "ep-98"
    assert "3月24日のAIニュース" in episode.summary_text


def test_fetch_episode_by_number_rejects_missing_number() -> None:
    client = FakePodcastClient()

    try:
        client.fetch_episode_by_number(123)
    except ValueError as exc:
        assert "episode_number 123 was not found in fetched data" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing episode number")
