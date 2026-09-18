"""Prevent overlapping active lounge bookings in PostgreSQL."""

from alembic import op

revision = "20260918_0003"
down_revision = "20260918_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT ex_active_lounge_booking_overlap
        EXCLUDE USING gist (
            booking_date WITH =,
            int4range(
                EXTRACT(HOUR FROM slot_start)::integer * 60
                    + EXTRACT(MINUTE FROM slot_start)::integer,
                EXTRACT(HOUR FROM slot_end)::integer * 60
                    + EXTRACT(MINUTE FROM slot_end)::integer
            ) WITH &&
        )
        WHERE (cancelled_at IS NULL)
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("ex_active_lounge_booking_overlap", "bookings", type_="exclude")
