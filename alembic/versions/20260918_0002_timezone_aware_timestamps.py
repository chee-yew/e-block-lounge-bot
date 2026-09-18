"""Use timezone-aware timestamps for audit and booking records."""

import sqlalchemy as sa

from alembic import op

revision = "20260918_0002"
down_revision = "20260918_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table, column in (
        ("users", "created_at"),
        ("bookings", "created_at"),
        ("bookings", "cancelled_at"),
        ("audit_logs", "created_at"),
    ):
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table, column in (
        ("users", "created_at"),
        ("bookings", "created_at"),
        ("bookings", "cancelled_at"),
        ("audit_logs", "created_at"),
    ):
        op.alter_column(
            table,
            column,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
