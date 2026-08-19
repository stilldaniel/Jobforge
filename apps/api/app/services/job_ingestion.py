from sqlalchemy.orm import Session

from app.job_sources.base import JobSource
from app.models.job import Job
from app.services.job_fingerprint import generate_job_fingerprint


def ingest_jobs(
    db: Session,
    source: JobSource,
) -> list[Job]:

    discovered_jobs = source.fetch_jobs()

    created_jobs = []

    for discovered_job in discovered_jobs:

        fingerprint = generate_job_fingerprint(
            title=discovered_job.title,
            company=discovered_job.company,
            application_url=discovered_job.application_url,
        )

        existing_job = (
            db.query(Job)
            .filter(Job.fingerprint == fingerprint)
            .first()
        )

        if existing_job:
            continue

        job = Job(
            title=discovered_job.title,
            company=discovered_job.company,
            description=discovered_job.description,
            location=discovered_job.location,
            work_type=discovered_job.work_type,
            salary_min=discovered_job.salary_min,
            salary_max=discovered_job.salary_max,
            application_url=discovered_job.application_url,
            source=discovered_job.source,
            fingerprint=fingerprint,
            posted_at=discovered_job.posted_at,
        )

        db.add(job)
        created_jobs.append(job)

    db.commit()

    for job in created_jobs:
        db.refresh(job)

    return created_jobs