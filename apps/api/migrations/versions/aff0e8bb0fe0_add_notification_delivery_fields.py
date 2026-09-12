"""add notification delivery fields

Revision ID: aff0e8bb0fe0
Revises: 3a19b37e61fc
Create Date: 2026-09-11 09:57:03.618001

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "aff0e8bb0fe0"
down_revision: Union[str, Sequence[str], None] = "3a19b37e61fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add channel as nullable first so existing rows can be migrated.
    op.add_column(
        "notifications",
        sa.Column(
            "channel",
            sa.String(length=50),
            nullable=True,
        ),
    )

    # Existing notifications start with zero delivery attempts.
    op.add_column(
        "notifications",
        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # Store the latest delivery error, if any.
    op.add_column(
        "notifications",
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
    )

    # Existing notifications use email as their delivery channel.
    op.execute(
        "UPDATE notifications "
        "SET channel = 'email' "
        "WHERE channel IS NULL"
    )

    # Now that all existing rows have a value, enforce NOT NULL.
    op.alter_column(
        "notifications",
        "channel",
        existing_type=sa.String(length=50),
        nullable=False,
    )

    # Remove the database-level default after existing rows are populated.
    # SQLAlchemy's model default will handle new notifications.
    op.alter_column(
        "notifications",
        "attempts",
        existing_type=sa.Integer(),
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "notifications",
        "last_error",
    )

    op.drop_column(
        "notifications",
        "attempts",
    )

    op.drop_column(
        "notifications",
        "channel",
    )