"""add salary currency and period to career profiles

Revision ID: d91e3b6c4a20
Revises: c4d8f2a7e915
Create Date: 2026-10-06 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd91e3b6c4a20'
down_revision: Union[str, Sequence[str], None] = 'c4d8f2a7e915'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('career_profiles', sa.Column('salary_currency', sa.String(length=3), nullable=True))
    op.add_column('career_profiles', sa.Column('salary_period', sa.String(length=10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('career_profiles', 'salary_period')
    op.drop_column('career_profiles', 'salary_currency')
