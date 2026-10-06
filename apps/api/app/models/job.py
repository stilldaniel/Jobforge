from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    required_skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    required_experience: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    remote_eligibility: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    work_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    salary_min: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    salary_max: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    salary_currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
    )

    salary_period: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    application_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Company + title key used to recognise the same job
    # listed on more than one platform.
    dedupe_key: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    job_matches = relationship(
        "JobMatch",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    saved_jobs = relationship(
        "SavedJob",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    applications = relationship(
        "Application",
        back_populates="job",
        cascade="all, delete-orphan",
    )