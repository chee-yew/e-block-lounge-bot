from datetime import date, time, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from e_block_bot.booking import BookingError, BookingService
from e_block_bot.config import Settings
from e_block_bot.db import init_database


@pytest.fixture
async def booking_service(tmp_path):
    database = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database}")
    await init_database(engine)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(TELEGRAM_BOT_TOKEN="test", DATABASE_URL=f"sqlite+aiosqlite:///{database}")
    service = BookingService(factory, settings)
    yield service
    await engine.dispose()


@pytest.mark.asyncio
async def test_availability_and_booking_conflict(booking_service: BookingService) -> None:
    booking_date = date.today() + timedelta(days=1)
    slot = booking_service.slot_for_duration(booking_date, time.min, 60)

    await booking_service.ensure_user(1, "one", "Resident")
    await booking_service.create_booking(1, booking_date, slot, "Study group")

    with pytest.raises(BookingError, match="overlaps"):
        await booking_service.create_booking(2, booking_date, slot, None)

    availability = await booking_service.availability(booking_date)
    assert availability[0][1] is False
    assert availability[1][1] is False

    with pytest.raises(BookingError, match="overlaps"):
        await booking_service.create_booking(
            2, booking_date, booking_service.slots_for_date(booking_date)[1], None
        )


@pytest.mark.asyncio
async def test_only_owner_or_admin_can_cancel(booking_service: BookingService) -> None:
    booking_date = date.today() + timedelta(days=1)
    slot = booking_service.slots_for_date(booking_date)[0]
    await booking_service.ensure_user(1, None, None)
    booking = await booking_service.create_booking(1, booking_date, slot, None)

    with pytest.raises(BookingError, match="own bookings"):
        await booking_service.cancel_booking(2, booking.id)

    await booking_service.cancel_booking(1, booking.id)
    assert await booking_service.user_bookings(1) == []

    replacement = await booking_service.create_booking(2, booking_date, slot, "Replacement")
    assert replacement.id != booking.id


@pytest.mark.asyncio
async def test_overnight_booking_counts_against_both_local_dates(
    booking_service: BookingService,
) -> None:
    start_date = date.today() + timedelta(days=1)
    overnight = booking_service.slot_for_duration(start_date, time(23, 30), 180)
    await booking_service.ensure_user(1, None, None)
    await booking_service.create_booking(1, start_date, overnight, None)

    next_day = start_date + timedelta(days=1)
    with pytest.raises(BookingError, match="3 hours"):
        await booking_service.create_booking(
            1, next_day, booking_service.slot_for_duration(next_day, time(2, 30), 60), None
        )
