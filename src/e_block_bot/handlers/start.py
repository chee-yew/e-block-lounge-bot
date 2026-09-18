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
        "Use these commands:\n"
        "/availability — choose a date and see current bookings\n"
        "/book — choose a date, start time, and duration\n"
        "/mybookings — see your future bookings\n"
        "/cancel BOOKING_ID — cancel your booking"
    )
