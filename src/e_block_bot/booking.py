"""Booking policy and service-layer rules."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from e_block_bot.config import Settings
from e_block_bot.models import AuditLog, Booking, User


class BookingError(ValueError):
    """Expected user-facing booking error."""


@dataclass(frozen=True)
class Slot:
    """One bookable local-time lounge slot."""

    start: time
    end: time

    def label(self) -> str:
        return f"{self.start:%H:%M}-{self.end:%H:%M}"


class BookingService:
    """Own booking rules and transaction boundaries."""

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], settings: Settings
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings

    def slots_for_date(self, booking_date: date) -> list[Slot]:
        """Return fixed slots for a date according to the configured local policy."""

        current = datetime.combine(booking_date, self.settings.lounge_open_time)
        close = datetime.combine(booking_date, self.settings.lounge_close_time)
        duration = timedelta(minutes=self.settings.slot_duration_minutes)
        slots: list[Slot] = []
        while current + duration <= close:
            slots.append(Slot(current.time(), (current + duration).time()))
            current += duration
        return slots

    async def availability(self, booking_date: date) -> list[tuple[Slot, bool]]:
        """Return configured slots and whether each is currently available."""

        slots = self.slots_for_date(booking_date)
        async with self.session_factory() as session:
            result = await session.scalars(
                select(Booking).where(
                    Booking.booking_date == booking_date,
                    Booking.cancelled_at.is_(None),
                )
            )
            booked = {(item.slot_start, item.slot_end) for item in result}
        return [(slot, (slot.start, slot.end) not in booked) for slot in slots]

    async def ensure_user(
        self, telegram_id: int, username: str | None, first_name: str | None
    ) -> None:
        """Insert or refresh the minimal Telegram identity."""

        async with self.session_factory() as session:
            user = await session.get(User, telegram_id)
            if user is None:
                session.add(User(telegram_id=telegram_id, username=username, first_name=first_name))
            else:
                user.username = username
                user.first_name = first_name
            await session.commit()

    async def create_booking(
        self,
        telegram_id: int,
        booking_date: date,
        slot: Slot,
        purpose: str | None,
    ) -> Booking:
        """Create a booking, relying on the unique constraint for race safety."""

        today = datetime.now(self.settings.timezone).date()
        if booking_date < today:
            raise BookingError("You cannot book a date in the past.")
        if slot not in self.slots_for_date(booking_date):
            raise BookingError("That is not one of the configured lounge slots.")
        async with self.session_factory() as session:
            booking = Booking(
                user_id=telegram_id,
                booking_date=booking_date,
                slot_start=slot.start,
                slot_end=slot.end,
                purpose=purpose[:500] if purpose else None,
            )
            session.add(booking)
            try:
                await session.commit()
            except IntegrityError as error:
                await session.rollback()
                raise BookingError("That slot was just booked by someone else.") from error
            await session.refresh(booking)
            return booking

    async def user_bookings(self, telegram_id: int, include_past: bool = False) -> list[Booking]:
        """Return a user's active future bookings."""

        today = datetime.now(self.settings.timezone).date()
        filters = [Booking.user_id == telegram_id, Booking.cancelled_at.is_(None)]
        if not include_past:
            filters.append(Booking.booking_date >= today)
        async with self.session_factory() as session:
            return list(
                (
                    await session.scalars(
                        select(Booking)
                        .where(*filters)
                        .order_by(Booking.booking_date, Booking.slot_start)
                    )
                ).all()
            )

    async def cancel_booking(
        self, telegram_id: int, booking_id: int, is_admin: bool = False
    ) -> Booking:
        """Cancel an owned booking or an admin-selected booking."""

        async with self.session_factory() as session:
            booking = await session.get(Booking, booking_id)
            if booking is None or booking.cancelled_at is not None:
                raise BookingError("Booking not found or already cancelled.")
            if not is_admin and booking.user_id != telegram_id:
                raise BookingError("You can only cancel your own bookings.")
            booking.cancelled_at = datetime.now(UTC)
            session.add(
                AuditLog(actor_id=telegram_id, action="cancel_booking", booking_id=booking.id)
            )
            await session.commit()
            return booking

    async def all_bookings(self) -> list[Booking]:
        """Return active bookings for administrators."""

        async with self.session_factory() as session:
            return list(
                (
                    await session.scalars(
                        select(Booking)
                        .where(Booking.cancelled_at.is_(None))
                        .order_by(Booking.booking_date, Booking.slot_start)
                    )
                ).all()
            )
