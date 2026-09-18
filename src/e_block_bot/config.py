"""Application configuration loaded from environment variables."""

from datetime import time
from functools import lru_cache
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator, model_validator
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
    database_url: str = Field(default="sqlite+aiosqlite:///./e_block_bot.db", alias="DATABASE_URL")
    admin_user_ids: str = Field(default="", alias="ADMIN_USER_IDS")
    lounge_open_time: time = Field(default=time(10, 0), alias="LOUNGE_OPEN_TIME")
    lounge_close_time: time = Field(default=time(22, 0), alias="LOUNGE_CLOSE_TIME")
    slot_duration_minutes: int = Field(default=120, alias="SLOT_DURATION_MINUTES", gt=0)

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

    @property
    def admin_ids(self) -> frozenset[int]:
        """Return configured Telegram administrator IDs."""

        return frozenset(
            int(value.strip()) for value in self.admin_user_ids.split(",") if value.strip()
        )

    @model_validator(mode="after")
    def validate_slot_window(self) -> "Settings":
        if self.lounge_close_time <= self.lounge_open_time:
            raise ValueError("LOUNGE_CLOSE_TIME must be later than LOUNGE_OPEN_TIME")
        total_minutes = (
            self.lounge_close_time.hour * 60
            + self.lounge_close_time.minute
            - self.lounge_open_time.hour * 60
            - self.lounge_open_time.minute
        )
        if total_minutes % self.slot_duration_minutes:
            raise ValueError("The lounge opening window must contain whole configured slots")
        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process."""

    # BaseSettings loads fields from the environment at runtime; mypy cannot
    # see that dynamic constructor behavior.
    return Settings()  # type: ignore[call-arg]


Token = Annotated[SecretStr, Field(description="Telegram bot token")]
