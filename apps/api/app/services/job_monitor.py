import logging

from sqlalchemy.orm import Session

from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.services.job_ingestion import ingest_jobs
from app.services.matching import calculate_match_score
from app.services.notification_service import create_notification_for_match
from app.job_sources.base import JobSource
from app.job_sources.registry import get_job_sources


logger = logging.getLogger(__name__)


def monitor_jobs(
    db: Session,
    sources: list[JobSource] | None = None,
) -> dict:
    """
    Run one complete JobForge monitoring cycle.

    The cycle:
        1. Discover jobs from configured sources
        2. Identify genuinely new jobs
        3. Match new jobs against user career profiles
        4. Create notifications for new matches

    Existing jobs are updated by ingestion but do not trigger
    new notifications.

    Individual source failures are isolated so that one failing
    source does not prevent other sources from being processed.
    """
    if sources is None:
        sources = get_job_sources()

    all_created_jobs: list[Job] = []
    total_updated_jobs = 0
    source_errors: list[str] = []

    for source in sources:
        source_name = source.__class__.__name__

        try:
            created_jobs, updated_jobs = ingest_jobs(
                db=db,
                source=source,
            )

            all_created_jobs.extend(created_jobs)
            total_updated_jobs += len(updated_jobs)

        except Exception as exc:
            logger.exception(
                "Job source failed during monitoring: %s",
                source_name,
            )

            source_errors.append(
                f"{source_name}: {str(exc)}"
            )

    if not all_created_jobs:
        return {
            "jobs_found": 0,
            "new_jobs": 0,
            "updated_jobs": total_updated_jobs,
            "matches_created": 0,
            "notifications_created": 0,
            "source_errors": source_errors,
        }

    profiles = db.query(CareerProfile).all()

    matches_created = 0
    notifications_created = 0

    for profile in profiles:
        for job in all_created_jobs:
            score, reasons = calculate_match_score(
                profile=profile,
                job=job,
            )

            existing_match = (
                db.query(JobMatch)
                .filter(
                    JobMatch.user_id == profile.user_id,
                    JobMatch.job_id == job.id,
                )
                .first()
            )

            if existing_match:
                match = existing_match
                match.score = score
                match.match_reasons = "; ".join(reasons)

            else:
                match = JobMatch(
                    user_id=profile.user_id,
                    job_id=job.id,
                    score=score,
                    match_reasons="; ".join(reasons),
                )

                db.add(match)
                db.flush()

                matches_created += 1

            notification = create_notification_for_match(
                db=db,
                match=match,
            )

            if notification:
                notifications_created += 1

    db.commit()

    return {
        "jobs_found": len(all_created_jobs),
        "new_jobs": len(all_created_jobs),
        "updated_jobs": total_updated_jobs,
        "matches_created": matches_created,
        "notifications_created": notifications_created,
        "source_errors": source_errors,
    }