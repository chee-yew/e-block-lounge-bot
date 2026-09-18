"""Telegram application construction."""

from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from e_block_bot.booking import BookingService
from e_block_bot.config import Settings
from e_block_bot.handlers.booking import create_booking_router
from e_block_bot.handlers.start import router as start_router


def create_dispatcher(
    session_factory: async_sessionmaker[AsyncSession], settings: Settings
) -> Dispatcher:
    """Build the dispatcher and register application routers."""

    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)
    dispatcher.include_router(
        create_booking_router(BookingService(session_factory, settings), settings)
    )
    return dispatcher


def create_bot(settings: Settings) -> Bot:
    """Create a Telegram bot client from validated settings."""

    return Bot(token=settings.telegram_bot_token.get_secret_value())
