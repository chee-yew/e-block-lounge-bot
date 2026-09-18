"""Persistent domain models."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, Time, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for application models."""


class User(Base):
    """Minimal Telegram identity stored for ownership and administration."""

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    bookings: Mapped[list[Booking]] = relationship(back_populates="user")


class Booking(Base):
    """A reservation for the single E Block lounge."""

    __tablename__ = "bookings"
    __table_args__ = (
        Index(
            "uq_active_lounge_slot",
            "booking_date",
            "slot_start",
            "slot_end",
            unique=True,
            postgresql_where=text("cancelled_at IS NULL"),
            sqlite_where=text("cancelled_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), index=True)
    booking_date: Mapped[date] = mapped_column(Date, index=True)
    slot_start: Mapped[time] = mapped_column(Time)
    slot_end: Mapped[time] = mapped_column(Time)
    purpose: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user: Mapped[User] = relationship(back_populates="bookings")


class AuditLog(Base):
    """Auditable record of privileged or destructive booking actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(100))
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
