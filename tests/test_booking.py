from datetime import date, timedelta

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
    slot = booking_service.slots_for_date(booking_date)[0]

    await booking_service.ensure_user(1, "one", "Resident")
    await booking_service.create_booking(1, booking_date, slot, "Study group")

    with pytest.raises(BookingError, match="overlaps"):
        await booking_service.create_booking(2, booking_date, slot, None)

    availability = await booking_service.availability(booking_date)
    assert availability[0] == (slot, False)

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
