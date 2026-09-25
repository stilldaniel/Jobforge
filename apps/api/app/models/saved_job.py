from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_id",
            name="uq_saved_jobs_user_job",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship(
        "User",
        back_populates="saved_jobs",
    )

    job = relationship(
        "Job",
        back_populates="saved_jobs",
    )