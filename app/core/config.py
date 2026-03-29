"""Application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings."""

    app_name: str = Field(default="AI News Verifier", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(default="sqlite:///./app.db", alias="DATABASE_URL")
    slack_webhook_url: str = Field(default="", alias="SLACK_WEBHOOK_URL")
    verifier_provider: str = Field(default="gemini", alias="VERIFIER_PROVIDER")
    perplexity_api_key: str = Field(default="", alias="PERPLEXITY_API_KEY")
    perplexity_model: str = Field(default="sonar", alias="PERPLEXITY_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    notify_score_threshold: int = Field(default=60, alias="NOTIFY_SCORE_THRESHOLD")
    state_file_path: Path = Field(default=Path(".state/last_run.json"), alias="STATE_FILE_PATH")
    podcast_rss_url: str = Field(
        default="https://podcasts.loudandfound.com/ainewstoday/podcast.xml",
        alias="PODCAST_RSS_URL",
    )
    podcast_apple_podcast_id: str = Field(default="1728333812", alias="PODCAST_APPLE_PODCAST_ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
