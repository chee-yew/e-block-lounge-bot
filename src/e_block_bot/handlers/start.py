"""Handlers for the bot's initial user interaction."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Welcome a resident and describe the bot's current scope."""

    await message.answer(
        "Welcome to the E Block Lounge Bot!\n\n"
        "Lounge booking is coming soon. For now, this bot is being prepared "
        "to show availability and manage your bookings."
    )
