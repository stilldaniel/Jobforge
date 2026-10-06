"""add multi-source job fields

Revision ID: b7c2e4a91f30
Revises: 20495087c2fc
Create Date: 2026-10-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.services.job_fingerprint import generate_dedupe_key


# revision identifiers, used by Alembic.
revision: str = 'b7c2e4a91f30'
down_revision: Union[str, Sequence[str], None] = '20495087c2fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('jobs', sa.Column('salary_currency', sa.String(length=3), nullable=True))
    op.add_column('jobs', sa.Column('salary_period', sa.String(length=20), nullable=True))
    op.add_column('jobs', sa.Column('dedupe_key', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_jobs_dedupe_key'), 'jobs', ['dedupe_key'], unique=False)

    # Backfill dedupe keys so jobs already stored are recognised when
    # another platform lists them.
    connection = op.get_bind()
    jobs = sa.table(
        'jobs',
        sa.column('id', sa.Integer),
        sa.column('title', sa.String),
        sa.column('company', sa.String),
        sa.column('dedupe_key', sa.String),
    )

    rows = connection.execute(
        sa.select(jobs.c.id, jobs.c.title, jobs.c.company)
    ).fetchall()

    for job_id, title, company in rows:
        connection.execute(
            jobs.update()
            .where(jobs.c.id == job_id)
            .values(dedupe_key=generate_dedupe_key(title=title, company=company))
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_jobs_dedupe_key'), table_name='jobs')
    op.drop_column('jobs', 'dedupe_key')
    op.drop_column('jobs', 'salary_period')
    op.drop_column('jobs', 'salary_currency')
