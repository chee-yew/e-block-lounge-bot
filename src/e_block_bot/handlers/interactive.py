"""Inline calendar, start-time, and duration selectors."""

import calendar
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from e_block_bot.booking import BookingError, BookingService, Slot
from e_block_bot.models import Booking, User


def calendar_keyboard(action: str, month: date) -> InlineKeyboardMarkup:
    """Build a month calendar for availability or booking."""

    rows = [
        [
            InlineKeyboardButton(
                text="‹", callback_data=f"cal:nav:{action}:{_month_value(month, -1)}"
            ),
            InlineKeyboardButton(text=month.strftime("%B %Y"), callback_data="cal:noop"),
            InlineKeyboardButton(
                text="›", callback_data=f"cal:nav:{action}:{_month_value(month, 1)}"
            ),
        ],
        [
            InlineKeyboardButton(text=day, callback_data="cal:noop")
            for day in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
        ],
    ]
    for week in calendar.monthcalendar(month.year, month.month):
        rows.append(
            [
                InlineKeyboardButton(
                    text=str(day) if day else " ",
                    callback_data=(
                        f"cal:date:{action}:{date(month.year, month.month, day).isoformat()}"
                        if day
                        else "cal:noop"
                    ),
                )
                for day in week
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_keyboard(
    booking_date: date, availability: Sequence[tuple[Slot, bool]]
) -> InlineKeyboardMarkup:
    """Build 30-minute start-time buttons for a selected date."""

    buttons = [
        InlineKeyboardButton(
            text=(f"✅ {slot.start:%H:%M}" if available else f"❌ {slot.start:%H:%M}"),
            callback_data=(
                f"time:{booking_date.isoformat()}:{slot.start:%H%M}" if available else "cal:noop"
            ),
        )
        for slot, available in availability
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[index : index + 4] for index in range(0, len(buttons), 4)]
    )


def duration_keyboard(
    booking_date: date, start: str, durations: Sequence[int]
) -> InlineKeyboardMarkup:
    """Build duration choices for a selected start time."""

    buttons = [
        InlineKeyboardButton(
            text=f"{minutes // 60}h" if minutes % 60 == 0 else f"{minutes}m",
            callback_data=f"duration:{booking_date.isoformat()}:{start}:{minutes}",
        )
        for minutes in durations
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[index : index + 3] for index in range(0, len(buttons), 3)]
    )


def create_interactive_router(service: BookingService) -> Router:
    """Create callback handlers for the interactive booking flow."""

    router = Router(name="interactive")

    @router.callback_query(F.data.startswith("cal:"))
    async def calendar_callback(callback: CallbackQuery) -> None:
        data = callback.data
        message = callback.message
        if data is None or data == "cal:noop" or not isinstance(message, Message):
            await callback.answer()
            return
        _, kind, action, value = data.split(":")
        if kind == "nav":
            await message.edit_reply_markup(
                reply_markup=calendar_keyboard(action, date.fromisoformat(f"{value}-01"))
            )
        elif kind == "date":
            selected_date = date.fromisoformat(value)
            if action == "availability":
                await message.edit_text(
                    availability_text(
                        service, selected_date, await service.bookings_for_date(selected_date)
                    ),
                    reply_markup=_book_date_keyboard(value),
                )
            else:
                await _show_start_times(message, service, selected_date)
        await callback.answer()

    @router.callback_query(F.data.startswith("bookdate:"))
    async def book_date_callback(callback: CallbackQuery) -> None:
        message = callback.message
        data = callback.data
        if data is None or not isinstance(message, Message):
            await callback.answer()
            return
        await _show_start_times(message, service, date.fromisoformat(data.split(":", 1)[1]))
        await callback.answer()

    @router.callback_query(F.data.startswith("time:"))
    async def time_callback(callback: CallbackQuery) -> None:
        message = callback.message
        data = callback.data
        if data is None or not isinstance(message, Message) or callback.from_user is None:
            await callback.answer()
            return
        _, date_value, time_value = data.split(":")
        booking_date = date.fromisoformat(date_value)
        durations = await service.available_durations(
            callback.from_user.id, booking_date, datetime.strptime(time_value, "%H%M").time()
        )
        if not durations:
            await callback.answer("No duration is available for that start time.", show_alert=True)
            return
        await message.edit_text(
            f"Choose the duration for {booking_date:%Y-%m-%d} "
            f"at {time_value[:2]}:{time_value[2:]}.",
            reply_markup=duration_keyboard(booking_date, time_value, durations),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("duration:"))
    async def duration_callback(callback: CallbackQuery) -> None:
        message = callback.message
        data = callback.data
        if data is None or not isinstance(message, Message) or callback.from_user is None:
            await callback.answer()
            return
        _, date_value, time_value, duration_value = data.split(":")
        booking_date = date.fromisoformat(date_value)
        start = datetime.strptime(time_value, "%H%M").time()
        slot = service.slot_for_duration(booking_date, start, int(duration_value))
        try:
            await service.ensure_user(
                callback.from_user.id,
                callback.from_user.username,
                callback.from_user.first_name,
            )
            booking = await service.create_booking(callback.from_user.id, booking_date, slot, None)
        except BookingError as error:
            await callback.answer(str(error), show_alert=True)
            return
        await message.edit_text(
            f"Booking confirmed: #{booking.id}\n"
            f"{booking.booking_date:%Y-%m-%d} "
            f"{booking.slot_start:%H:%M}-{booking.slot_end:%H:%M}"
        )
        await callback.answer("Booking confirmed")

    return router


async def _show_start_times(message: Message, service: BookingService, selected_date: date) -> None:
    rows = await service.availability(selected_date)
    await message.edit_text(
        f"Choose a 30-minute start time for {selected_date:%Y-%m-%d}.",
        reply_markup=time_keyboard(selected_date, rows),
    )


def _book_date_keyboard(value: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Book this date", callback_data=f"bookdate:{value}")]
        ]
    )


def _month_value(month: date, offset: int) -> str:
    month_index = month.year * 12 + month.month - 1 + offset
    return f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"


def availability_text(
    service: BookingService, selected_date: date, rows: Sequence[tuple[Booking, User]]
) -> str:
    if not rows:
        return f"No bookings for {selected_date:%Y-%m-%d}."
    lines = [f"Bookings for {selected_date:%Y-%m-%d}:"]
    day_start = datetime.combine(selected_date, time.min, tzinfo=service.settings.timezone)
    day_end = day_start + timedelta(days=1)
    for booking, user in rows:
        handle = f"@{user.username}" if user.username else (user.first_name or "resident")
        start = service._aware(booking.start_at).astimezone(service.settings.timezone)
        end = service._aware(booking.end_at).astimezone(service.settings.timezone)
        start = max(start, day_start)
        end = min(end, day_end)
        lines.append(f"{start:%H:%M}-{end:%H:%M} — {handle}")
    return "\n".join(lines)
