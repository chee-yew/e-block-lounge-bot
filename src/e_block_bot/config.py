"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the Telegram bot."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    telegram_bot_token: SecretStr = Field(alias="TELEGRAM_BOT_TOKEN")
    e_block_timezone: str = Field(default="Asia/Singapore", alias="E_BLOCK_TIMEZONE")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    @field_validator("e_block_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError(f"Unknown timezone: {value}") from error
        return value

    @property
    def timezone(self) -> ZoneInfo:
        """Return the configured timezone for date and time calculations."""

        return ZoneInfo(self.e_block_timezone)


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process."""

    return Settings()


Token = Annotated[SecretStr, Field(description="Telegram bot token")]
