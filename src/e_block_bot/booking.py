"""Booking policy and service-layer rules."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from e_block_bot.config import Settings
from e_block_bot.models import AuditLog, Booking, User


class BookingError(ValueError):
    """Expected user-facing booking error."""


@dataclass(frozen=True)
class Slot:
    """A local-time booking interval."""

    start: time
    end: time

    def label(self) -> str:
        suffix = " (+1 day)" if self.end <= self.start else ""
        return f"{self.start:%H:%M}-{self.end:%H:%M}{suffix}"


class BookingService:
    """Own booking rules and transaction boundaries."""

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], settings: Settings
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings

    def slots_for_date(self, booking_date: date) -> list[Slot]:
        """Return every 30-minute start option in the 24-hour day."""

        increment = timedelta(minutes=self.settings.slot_increment_minutes)
        duration = timedelta(minutes=self.settings.slot_increment_minutes)
        return [
            Slot(current.time(), (current + duration).time())
            for _ in range(24 * 60 // self.settings.slot_increment_minutes)
            for current in [datetime.combine(booking_date, time.min) + _ * increment]
        ]

    def slot_for_duration(self, booking_date: date, start: time, duration_minutes: int) -> Slot:
        """Build and validate a slot, including one that crosses midnight."""

        if duration_minutes < self.settings.slot_increment_minutes:
            raise BookingError("Bookings must be at least 30 minutes long.")
        if duration_minutes > self.settings.max_daily_booking_minutes:
            raise BookingError("A booking cannot be longer than 3 hours.")
        if start.minute % self.settings.slot_increment_minutes:
            raise BookingError("Start times must use 30-minute increments.")
        end = datetime.combine(date.today(), start) + timedelta(minutes=duration_minutes)
        return Slot(start, end.time())

    async def availability(self, booking_date: date) -> list[tuple[Slot, bool]]:
        """Return 30-minute starts and whether each can be booked."""

        rows = await self._active_bookings_near(booking_date)
        now = datetime.now(self.settings.timezone)
        result: list[tuple[Slot, bool]] = []
        for slot in self.slots_for_date(booking_date):
            start_at, end_at = self._local_interval(booking_date, slot)
            available = start_at > now and not any(
                self._overlaps(start_at, end_at, item) for item in rows
            )
            result.append((slot, available))
        return result

    async def available_durations(
        self, telegram_id: int, booking_date: date, start: time
    ) -> list[int]:
        """Return duration choices that fit conflicts and the daily allowance."""

        rows = await self._active_bookings_near(booking_date)
        user_rows = await self.user_bookings(telegram_id, include_past=True)
        choices: list[int] = []
        for duration in range(
            self.settings.slot_increment_minutes,
            self.settings.max_daily_booking_minutes + 1,
            self.settings.slot_increment_minutes,
        ):
            slot = self.slot_for_duration(booking_date, start, duration)
            start_at, end_at = self._local_interval(booking_date, slot)
            if any(self._overlaps(start_at, end_at, item) for item in rows):
                continue
            if any(
                self._daily_minutes(user_rows, day)
                + self._interval_minutes_on_day(start_at, end_at, day)
                > self.settings.max_daily_booking_minutes
                for day in self._affected_dates(start_at, end_at)
            ):
                continue
            choices.append(duration)
        return choices

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
        """Create a booking with overlap and per-day duration protection."""

        now = datetime.now(self.settings.timezone)
        if booking_date < now.date() or (booking_date == now.date() and slot.start <= now.time()):
            raise BookingError("That start time has already passed.")
        start_at, end_at = self._local_interval(booking_date, slot)
        if (end_at - start_at).total_seconds() / 60 > self.settings.max_daily_booking_minutes:
            raise BookingError("A booking cannot be longer than 3 hours.")
        affected_dates = self._affected_dates(start_at, end_at)
        async with self.session_factory() as session:
            if session.get_bind().dialect.name == "postgresql":
                for affected_date in affected_dates:
                    await session.execute(
                        text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                        {"key": f"booking:{telegram_id}:{affected_date.isoformat()}"},
                    )
            existing = list(
                (await session.scalars(select(Booking).where(Booking.cancelled_at.is_(None)))).all()
            )
            if any(self._overlaps(start_at, end_at, item) for item in existing):
                raise BookingError("That time overlaps an existing booking.")
            user_existing = [item for item in existing if item.user_id == telegram_id]
            if any(
                self._daily_minutes(user_existing, affected_date)
                + self._interval_minutes_on_day(start_at, end_at, affected_date)
                > self.settings.max_daily_booking_minutes
                for affected_date in affected_dates
            ):
                raise BookingError("You can book at most 3 hours per calendar day.")
            booking = Booking(
                user_id=telegram_id,
                booking_date=booking_date,
                slot_start=slot.start,
                slot_end=slot.end,
                start_at=start_at,
                end_at=end_at,
                purpose=purpose[:500] if purpose else None,
            )
            session.add(booking)
            try:
                await session.commit()
            except IntegrityError as error:
                await session.rollback()
                raise BookingError("That time was just booked by someone else.") from error
            await session.refresh(booking)
            return booking

    async def user_bookings(self, telegram_id: int, include_past: bool = False) -> list[Booking]:
        """Return a user's active bookings."""

        filters = [Booking.user_id == telegram_id, Booking.cancelled_at.is_(None)]
        async with self.session_factory() as session:
            return list(
                (
                    await session.scalars(
                        select(Booking).where(*filters).order_by(Booking.start_at)
                    )
                ).all()
            )

    async def bookings_for_date(self, booking_date: date) -> list[tuple[Booking, User]]:
        """Return bookings touching a date with the resident display identity."""

        rows = await self._active_bookings_near(booking_date)
        async with self.session_factory() as session:
            users = {
                user.telegram_id: user
                for user in (
                    await session.scalars(
                        select(User).where(User.telegram_id.in_([row.user_id for row in rows]))
                    )
                ).all()
            }
        return [(row, users[row.user_id]) for row in rows if row.user_id in users]

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
                        .order_by(Booking.start_at)
                    )
                ).all()
            )

    async def _active_bookings_near(self, booking_date: date) -> list[Booking]:
        """Load active bookings that could touch a local calendar date."""

        async with self.session_factory() as session:
            return list(
                (
                    await session.scalars(
                        select(Booking).where(
                            Booking.cancelled_at.is_(None),
                            Booking.booking_date.in_(
                                (booking_date, booking_date - timedelta(days=1))
                            ),
                        )
                    )
                ).all()
            )

    def _local_interval(self, booking_date: date, slot: Slot) -> tuple[datetime, datetime]:
        timezone = self.settings.timezone
        start = datetime.combine(booking_date, slot.start, tzinfo=timezone)
        end_date = booking_date + timedelta(days=1) if slot.end <= slot.start else booking_date
        end = datetime.combine(end_date, slot.end, tzinfo=timezone)
        return start, end

    def _overlaps(self, start: datetime, end: datetime, booking: Booking) -> bool:
        existing_start = self._aware(booking.start_at)
        existing_end = self._aware(booking.end_at)
        return existing_start < end and start < existing_end

    def _aware(self, value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=self.settings.timezone)

    def _affected_dates(self, start: datetime, end: datetime) -> list[date]:
        last_date = (end - timedelta(microseconds=1)).date()
        return [
            start.date() + timedelta(days=offset)
            for offset in range((last_date - start.date()).days + 1)
        ]

    def _interval_minutes_on_day(self, start: datetime, end: datetime, day: date) -> int:
        day_start = datetime.combine(day, time.min, tzinfo=self.settings.timezone)
        day_end = day_start + timedelta(days=1)
        overlap = max(timedelta(0), min(end, day_end) - max(start, day_start))
        return int(overlap.total_seconds() // 60)

    def _daily_minutes(self, bookings: list[Booking], day: date) -> int:
        return sum(
            self._interval_minutes_on_day(self._aware(item.start_at), self._aware(item.end_at), day)
            for item in bookings
        )
