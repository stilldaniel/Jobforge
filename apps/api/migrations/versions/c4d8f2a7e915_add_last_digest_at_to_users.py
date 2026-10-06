"""add last digest at to users

Revision ID: c4d8f2a7e915
Revises: b7c2e4a91f30
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d8f2a7e915'
down_revision: Union[str, Sequence[str], None] = 'b7c2e4a91f30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('last_digest_at', sa.DateTime(timezone=True), nullable=True))

    # Treat existing users as having had today's digest, so deploying
    # doesn't send everyone a digest straight away; each gets the next
    # one at the digest time in their own timezone.
    op.execute(sa.text('UPDATE users SET last_digest_at = CURRENT_TIMESTAMP'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'last_digest_at')
