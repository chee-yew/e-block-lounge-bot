"""Telegram commands for lounge availability and bookings."""

from collections.abc import Sequence
from datetime import date, datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from e_block_bot.booking import BookingError, BookingService
from e_block_bot.config import Settings
from e_block_bot.models import Booking


def create_booking_router(service: BookingService, settings: Settings) -> Router:
    """Build handlers with their application dependencies."""

    router = Router(name="booking")

    @router.message(Command("availability"))
    async def availability(message: Message) -> None:
        if message.chat.type != "private":
            await message.answer("Please use this command in a private chat with the bot.")
            return
        raw_date = _arguments(message)
        try:
            booking_date = date.fromisoformat(raw_date) if raw_date else _today(settings)
        except ValueError:
            await message.answer("Use the date format YYYY-MM-DD.")
            return
        if booking_date < _today(settings):
            await message.answer("Please choose today or a future date.")
            return
        availability_rows = await service.availability(booking_date)
        lines = [f"Lounge availability for {booking_date:%Y-%m-%d}:"]
        lines.extend(
            f"{slot.label()} — {'available' if available else 'booked'}"
            for slot, available in availability_rows
        )
        await message.answer("\n".join(lines) + "\n\nTo book: /book YYYY-MM-DD HH:MM [purpose]")

    @router.message(Command("book"))
    async def book(message: Message) -> None:
        if message.chat.type != "private" or message.from_user is None:
            await message.answer("Please book in a private chat with the bot.")
            return
        parts = _arguments(message).split(maxsplit=2)
        if len(parts) < 2:
            await message.answer("Usage: /book YYYY-MM-DD HH:MM [optional purpose]")
            return
        try:
            booking_date = date.fromisoformat(parts[0])
            start = datetime.strptime(parts[1], "%H:%M").time()
        except ValueError:
            await message.answer("Use /book YYYY-MM-DD HH:MM [optional purpose].")
            return
        slot = next(
            (
                candidate
                for candidate in service.slots_for_date(booking_date)
                if candidate.start == start
            ),
            None,
        )
        if slot is None:
            await message.answer("That start time is not one of the configured two-hour slots.")
            return
        try:
            await service.ensure_user(
                message.from_user.id, message.from_user.username, message.from_user.first_name
            )
            booking = await service.create_booking(
                message.from_user.id, booking_date, slot, parts[2] if len(parts) == 3 else None
            )
        except BookingError as error:
            await message.answer(str(error))
            return
        await message.answer(
            f"Booking confirmed: #{booking.id}\n"
            f"{booking.booking_date:%Y-%m-%d} "
            f"{booking.slot_start:%H:%M}-{booking.slot_end:%H:%M}"
        )

    @router.message(Command("mybookings"))
    async def my_bookings(message: Message) -> None:
        if message.chat.type != "private" or message.from_user is None:
            await message.answer("Please use this command in a private chat with the bot.")
            return
        bookings = await service.user_bookings(message.from_user.id)
        await message.answer(_format_bookings(bookings, "You have no future bookings."))

    @router.message(Command("cancel"))
    async def cancel(message: Message) -> None:
        if message.chat.type != "private" or message.from_user is None:
            await message.answer("Please use this command in a private chat with the bot.")
            return
        try:
            booking_id = int(_arguments(message))
            booking = await service.cancel_booking(message.from_user.id, booking_id)
        except (ValueError, BookingError):
            await message.answer(
                "Usage: /cancel BOOKING_ID. You can only cancel your own active booking."
            )
            return
        await message.answer(f"Booking #{booking.id} cancelled.")

    @router.message(Command("admin_bookings"))
    async def admin_bookings(message: Message) -> None:
        if not _is_admin(message, settings):
            await message.answer("This command is only available to configured administrators.")
            return
        bookings = await service.all_bookings()
        await message.answer(_format_bookings(bookings, "There are no active bookings."))

    @router.message(Command("admin_cancel"))
    async def admin_cancel(message: Message) -> None:
        if not _is_admin(message, settings) or message.from_user is None:
            await message.answer("This command is only available to configured administrators.")
            return
        try:
            booking_id = int(_arguments(message))
            booking = await service.cancel_booking(message.from_user.id, booking_id, is_admin=True)
        except (ValueError, BookingError):
            await message.answer("Usage: /admin_cancel BOOKING_ID")
            return
        await message.answer(f"Booking #{booking.id} cancelled by administrator.")

    return router


def _arguments(message: Message) -> str:
    """Extract text following a command."""

    text = message.text or ""
    return text.partition(" ")[2].strip()


def _today(settings: Settings) -> date:
    return datetime.now(settings.timezone).date()


def _is_admin(message: Message, settings: Settings) -> bool:
    return message.from_user is not None and message.from_user.id in settings.admin_ids


def _format_bookings(bookings: Sequence[Booking], empty_message: str) -> str:
    if not bookings:
        return empty_message
    return "\n".join(
        f"#{booking.id} — {booking.booking_date:%Y-%m-%d} "
        f"{booking.slot_start:%H:%M}-{booking.slot_end:%H:%M}"
        + (f" — {booking.purpose}" if booking.purpose else "")
        for booking in bookings
    )
