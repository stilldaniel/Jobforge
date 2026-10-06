import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.services.job_ingestion import ingest_jobs
from app.services.matching import calculate_match_score
from app.services.notification_service import create_notification_for_match
from app.services.search_criteria import build_search_criteria, is_relevant
from app.job_sources.base import JobSource
from app.job_sources.registry import get_job_sources


logger = logging.getLogger(__name__)


# When each source was last fetched, keyed by class name. Kept in memory,
# so a restart allows one early fetch per source.
_last_fetched_at: dict[str, datetime] = {}


def _is_due(source: JobSource, now: datetime) -> bool:
    last_fetched_at = _last_fetched_at.get(source.__class__.__name__)

    if last_fetched_at is None or not source.min_interval_minutes:
        return True

    return now - last_fetched_at >= timedelta(
        minutes=source.min_interval_minutes
    )


def monitor_jobs(
    db: Session,
    sources: list[JobSource] | None = None,
) -> dict:
    """
    Run one complete JobForge monitoring cycle.

    The cycle:
        1. Build search terms from users' career profiles
        2. Discover jobs from configured sources
        3. Identify genuinely new jobs
        4. Match new jobs against user career profiles
        5. Create notifications for new matches

    Existing jobs are updated by ingestion but do not trigger
    new notifications. A job already supplied by another platform
    is skipped.

    Individual source failures are isolated so that one failing
    source does not prevent other sources from being processed.
    """

    if sources is None:
        sources = get_job_sources()

    profiles = db.query(CareerProfile).all()
    criteria = build_search_criteria(profiles)

    now = datetime.now(timezone.utc)

    all_created_jobs: list[Job] = []
    total_updated_jobs = 0
    total_duplicate_jobs = 0
    total_irrelevant_jobs = 0
    sources_skipped: list[str] = []
    source_errors: list[str] = []

    for source in sources:
        source_name = source.__class__.__name__

        if not _is_due(source, now):
            sources_skipped.append(source_name)
            continue

        # A broad feed with no profiles to filter against would only
        # store jobs nobody can be matched to.
        if source.filter_by_relevance and criteria.is_empty:
            sources_skipped.append(source_name)
            continue

        source.search_queries = criteria.queries

        try:
            discovered_jobs = source.fetch_jobs()

            # Count the fetch even if ingestion fails below, so that a
            # failing source is not retried more often than allowed.
            _last_fetched_at[source_name] = now

            if source.filter_by_relevance:
                relevant_jobs = [
                    job
                    for job in discovered_jobs
                    if is_relevant(job, criteria)
                ]
                total_irrelevant_jobs += (
                    len(discovered_jobs) - len(relevant_jobs)
                )
                discovered_jobs = relevant_jobs

            result = ingest_jobs(
                db=db,
                source=source,
                discovered_jobs=discovered_jobs,
            )

            all_created_jobs.extend(result.created_jobs)
            total_updated_jobs += len(result.updated_jobs)
            total_duplicate_jobs += result.duplicate_jobs

        except Exception as exc:
            # A failed fetch leaves the session untouched; a failed
            # database write leaves it unusable until rolled back.
            if db.in_transaction() and not db.is_active:
                db.rollback()

            logger.exception(
                "Job source failed during monitoring: %s",
                source_name,
            )

            source_errors.append(
                f"{source_name}: {str(exc)}"
            )

    summary = {
        "jobs_found": len(all_created_jobs),
        "new_jobs": len(all_created_jobs),
        "updated_jobs": total_updated_jobs,
        "duplicate_jobs": total_duplicate_jobs,
        "irrelevant_jobs": total_irrelevant_jobs,
        "matches_created": 0,
        "notifications_created": 0,
        "sources_skipped": sources_skipped,
        "source_errors": source_errors,
    }

    if not all_created_jobs:
        return summary

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

    summary["matches_created"] = matches_created
    summary["notifications_created"] = notifications_created

    return summary
