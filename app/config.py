from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")

    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_db: str = Field(default="ielts_speaking", alias="MONGODB_DB")

    anthropic_api_key: str = Field(alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-sonnet-5", alias="CLAUDE_MODEL")

    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    stt_model: str = Field(default="gpt-4o-mini-transcribe", alias="STT_MODEL")

    default_timezone: str = Field(default="UTC", alias="DEFAULT_TIMEZONE")
    max_voice_duration_seconds: int = Field(default=120, alias="MAX_VOICE_DURATION_SECONDS")

    free_attempts_limit: int = Field(default=3, alias="FREE_ATTEMPTS_LIMIT")
    stars_price_single_question: int = Field(default=50, alias="STARS_PRICE_SINGLE_QUESTION")
    stars_price_weekly: int = Field(default=150, alias="STARS_PRICE_WEEKLY")
    stars_price_unlimited: int = Field(default=1000, alias="STARS_PRICE_UNLIMITED")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8080, alias="APP_PORT")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
