"""Telegram application construction."""

from aiogram import Bot, Dispatcher

from e_block_bot.config import Settings
from e_block_bot.handlers.start import router as start_router


def create_dispatcher() -> Dispatcher:
    """Build the dispatcher and register application routers."""

    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)
    return dispatcher


def create_bot(settings: Settings) -> Bot:
    """Create a Telegram bot client from validated settings."""

    return Bot(token=settings.telegram_bot_token.get_secret_value())
