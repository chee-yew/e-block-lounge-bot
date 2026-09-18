"""Store booking intervals as timestamps to support overnight bookings."""

import sqlalchemy as sa

from alembic import op

revision = "20260918_0004"
down_revision = "20260918_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_constraint("ex_active_lounge_booking_overlap", "bookings", type_="exclude")
    op.add_column("bookings", sa.Column("start_at", sa.DateTime(timezone=True)))
    op.add_column("bookings", sa.Column("end_at", sa.DateTime(timezone=True)))
    op.execute(
        """
        UPDATE bookings
        SET start_at = (booking_date + slot_start) AT TIME ZONE 'Asia/Singapore',
            end_at = (booking_date + slot_end) AT TIME ZONE 'Asia/Singapore'
        """
    )
    op.alter_column("bookings", "start_at", nullable=False)
    op.alter_column("bookings", "end_at", nullable=False)
    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT ex_active_lounge_booking_overlap
        EXCLUDE USING gist (tstzrange(start_at, end_at, '[)') WITH &&)
        WHERE (cancelled_at IS NULL)
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_constraint("ex_active_lounge_booking_overlap", "bookings", type_="exclude")
    op.drop_column("bookings", "end_at")
    op.drop_column("bookings", "start_at")
