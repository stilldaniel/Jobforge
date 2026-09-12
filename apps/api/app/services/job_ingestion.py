from sqlalchemy.orm import Session

from app.job_sources.base import JobSource
from app.models.job import Job
from app.services.job_fingerprint import generate_job_fingerprint
from app.services.job_requirements import extract_requirements


def ingest_jobs(
    db: Session,
    source: JobSource,
) -> tuple[list[Job], list[Job]]:
    """
    Fetch jobs from a source and synchronize them with the database.

    Returns:
        tuple:
            - created_jobs: newly created jobs
            - updated_jobs: existing jobs that were updated
    """

    discovered_jobs = source.fetch_jobs()

    created_jobs: list[Job] = []
    updated_jobs: list[Job] = []

    for discovered_job in discovered_jobs:

        # --------------------------------------------------
        # GENERATE FINGERPRINT
        # --------------------------------------------------

        fingerprint = generate_job_fingerprint(
            title=discovered_job.title,
            company=discovered_job.company,
            application_url=discovered_job.application_url,
        )

        print(
            f"[INGEST] {discovered_job.company} | "
            f"{discovered_job.title} | "
            f"{discovered_job.application_url} | "
            f"{fingerprint}"
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

            existing_job.title = discovered_job.title
            existing_job.company = discovered_job.company
            existing_job.description = discovered_job.description

            existing_job.required_skills = requirements[
                "required_skills"
            ]

            existing_job.required_experience = requirements[
                "required_experience"
            ]

            existing_job.location = discovered_job.location

            existing_job.remote_eligibility = (
                discovered_job.remote_eligibility
            )

            existing_job.work_type = discovered_job.work_type
            existing_job.salary_min = discovered_job.salary_min
            existing_job.salary_max = discovered_job.salary_max
            existing_job.application_url = (
                discovered_job.application_url
            )
            existing_job.posted_at = discovered_job.posted_at

            updated_jobs.append(existing_job)

            continue

        # --------------------------------------------------
        # NEW JOB
        # --------------------------------------------------

        job = Job(
            title=discovered_job.title,
            company=discovered_job.company,
            description=discovered_job.description,
            required_skills=requirements["required_skills"],
            required_experience=requirements["required_experience"],
            location=discovered_job.location,
            remote_eligibility=discovered_job.remote_eligibility,
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

    return created_jobs, updated_jobs