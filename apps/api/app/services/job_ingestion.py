import logging
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.job_sources.base import DiscoveredJob, JobSource
from app.models.job import Job
from app.services.job_fingerprint import (
    generate_dedupe_key,
    generate_job_fingerprint,
    generate_listing_fingerprint,
)
from app.services.job_requirements import extract_requirements


logger = logging.getLogger(__name__)


class IngestionResult(NamedTuple):
    created_jobs: list[Job]
    updated_jobs: list[Job]
    # Jobs skipped because another platform already supplied them.
    duplicate_jobs: int


def ingest_jobs(
    db: Session,
    source: JobSource,
    discovered_jobs: list[DiscoveredJob] | None = None,
) -> IngestionResult:
    """
    Fetch jobs from a source and synchronize them with the database.

    A job is matched to an existing record in two ways:
        - Same fingerprint (title + company + URL): the same listing
          seen again, so the record is updated.
        - Same dedupe key (title + company) from a different source:
          the same job posted on another platform, so it is skipped.

    Pass `discovered_jobs` to ingest jobs that were already fetched.
    """

    if discovered_jobs is None:
        discovered_jobs = source.fetch_jobs()

    created_jobs: list[Job] = []
    updated_jobs: list[Job] = []
    duplicate_jobs = 0

    seen_fingerprints: set[str] = set()

    for discovered_job in discovered_jobs:
        # --------------------------------------------------
        # GENERATE KEYS
        # --------------------------------------------------

        if discovered_job.external_id:
            fingerprint = generate_listing_fingerprint(
                source=discovered_job.source,
                external_id=discovered_job.external_id,
            )
        else:
            fingerprint = generate_job_fingerprint(
                title=discovered_job.title,
                company=discovered_job.company,
                application_url=discovered_job.application_url,
            )

        dedupe_key = generate_dedupe_key(
            title=discovered_job.title,
            company=discovered_job.company,
        )

        # Feeds that are searched once per query can return the
        # same listing more than once.
        if fingerprint in seen_fingerprints:
            continue

        seen_fingerprints.add(fingerprint)

        logger.debug(
            "[INGEST] %s | %s | %s | %s",
            discovered_job.company,
            discovered_job.title,
            discovered_job.application_url,
            fingerprint,
        )

        # --------------------------------------------------
        # EXTRACT REQUIREMENTS
        # --------------------------------------------------

        requirements = extract_requirements(
            title=discovered_job.title,
            description=discovered_job.description,
        )

        # --------------------------------------------------
        # FIND EXISTING JOB
        # --------------------------------------------------

        existing_job = (
            db.query(Job)
            .filter(Job.fingerprint == fingerprint)
            .first()
        )

        # --------------------------------------------------
        # EXISTING JOB
        # --------------------------------------------------

        if existing_job:
            _apply_discovered_fields(
                existing_job,
                discovered_job,
                requirements,
            )
            existing_job.dedupe_key = dedupe_key

            updated_jobs.append(existing_job)
            continue

        # --------------------------------------------------
        # SAME JOB FROM ANOTHER PLATFORM
        # --------------------------------------------------

        cross_source_duplicate = (
            db.query(Job.id)
            .filter(
                Job.dedupe_key == dedupe_key,
                Job.source != discovered_job.source,
            )
            .first()
        )

        if cross_source_duplicate:
            duplicate_jobs += 1
            continue

        # --------------------------------------------------
        # NEW JOB
        # --------------------------------------------------

        job = Job(
            source=discovered_job.source,
            fingerprint=fingerprint,
            dedupe_key=dedupe_key,
        )

        _apply_discovered_fields(
            job,
            discovered_job,
            requirements,
        )

        db.add(job)
        created_jobs.append(job)

    # --------------------------------------------------
    # SAVE CHANGES
    # --------------------------------------------------

    db.commit()

    # --------------------------------------------------
    # REFRESH DATABASE OBJECTS
    # --------------------------------------------------

    for job in created_jobs:
        db.refresh(job)

    for job in updated_jobs:
        db.refresh(job)

    return IngestionResult(
        created_jobs=created_jobs,
        updated_jobs=updated_jobs,
        duplicate_jobs=duplicate_jobs,
    )


def _apply_discovered_fields(
    job: Job,
    discovered_job: DiscoveredJob,
    requirements: dict,
) -> None:
    job.title = discovered_job.title
    job.company = discovered_job.company
    job.description = discovered_job.description
    job.required_skills = requirements["required_skills"]
    job.required_experience = requirements["required_experience"]
    job.location = discovered_job.location
    job.remote_eligibility = discovered_job.remote_eligibility
    job.work_type = discovered_job.work_type
    job.salary_min = discovered_job.salary_min
    job.salary_max = discovered_job.salary_max
    job.salary_currency = discovered_job.salary_currency
    job.salary_period = discovered_job.salary_period
    job.application_url = discovered_job.application_url
    job.posted_at = discovered_job.posted_at
