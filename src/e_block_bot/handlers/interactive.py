"""Inline calendar and time selectors for the booking workflow."""

import calendar
from collections.abc import Sequence
from datetime import date, datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from e_block_bot.booking import BookingError, BookingService, Slot


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


def time_keyboard(booking_date: date, availability: list[tuple[str, bool]]) -> InlineKeyboardMarkup:
    """Build 30-minute start-time buttons for a selected date."""

    buttons = [
        InlineKeyboardButton(
            text=(f"✅ {label}" if available else f"❌ {label}"),
            callback_data=(
                f"time:{booking_date.isoformat()}:{label[:5].replace(':', '')}"
                if available
                else "cal:noop"
            ),
        )
        for label, available in availability
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[index : index + 3] for index in range(0, len(buttons), 3)]
    )


def create_interactive_router(service: BookingService) -> Router:
    """Create callback handlers for calendars and time selection."""

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
            selected_month = date.fromisoformat(f"{value}-01")
            await message.edit_reply_markup(reply_markup=calendar_keyboard(action, selected_month))
        elif kind == "date":
            selected_date = date.fromisoformat(value)
            rows = await service.availability(selected_date)
            if action == "availability":
                await message.edit_text(
                    _availability_text(selected_date, rows),
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Book this date", callback_data=f"bookdate:{value}"
                                )
                            ]
                        ]
                    ),
                )
            else:
                await message.edit_text(
                    f"Choose a 30-minute start time for {selected_date:%Y-%m-%d}.\n"
                    "Each booking lasts two hours.",
                    reply_markup=time_keyboard(
                        selected_date, [(slot.label(), available) for slot, available in rows]
                    ),
                )
        await callback.answer()

    @router.callback_query(F.data.startswith("bookdate:"))
    async def book_date_callback(callback: CallbackQuery) -> None:
        message = callback.message
        data = callback.data
        if data is None or not isinstance(message, Message):
            await callback.answer()
            return
        selected_date = date.fromisoformat(data.split(":", 1)[1])
        rows = await service.availability(selected_date)
        await message.edit_text(
            f"Choose a 30-minute start time for {selected_date:%Y-%m-%d}.\n"
            "Each booking lasts two hours.",
            reply_markup=time_keyboard(
                selected_date, [(slot.label(), available) for slot, available in rows]
            ),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("time:"))
    async def time_callback(callback: CallbackQuery) -> None:
        message = callback.message
        data = callback.data
        if data is None or not isinstance(message, Message):
            await callback.answer()
            return
        _, date_value, time_value = data.split(":")
        booking_date = date.fromisoformat(date_value)
        start = datetime.strptime(time_value, "%H%M").time()
        slot = next(
            (
                candidate
                for candidate in service.slots_for_date(booking_date)
                if candidate.start == start
            ),
            None,
        )
        if slot is None or callback.from_user is None:
            await callback.answer("That time is no longer available.", show_alert=True)
            return
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


def _month_value(month: date, offset: int) -> str:
    month_index = month.year * 12 + month.month - 1 + offset
    return f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"


def _availability_text(selected_date: date, rows: Sequence[tuple[Slot, bool]]) -> str:
    lines = [f"Lounge availability for {selected_date:%Y-%m-%d}:"]
    lines.extend(
        f"{slot.label()} — {'available' if available else 'booked'}" for slot, available in rows
    )
    return "\n".join(lines)
