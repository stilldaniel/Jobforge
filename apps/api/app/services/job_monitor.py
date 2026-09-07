from sqlalchemy.orm import Session

from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.services.job_ingestion import ingest_jobs
from app.services.matching import calculate_match_score
from app.services.notification_service import (
    create_notification_for_match,
)
from app.job_sources.mock import MockJobSource


def monitor_jobs(db: Session) -> dict:
    """
    Run one complete JobForge monitoring cycle.

    The cycle:
        1. Discover jobs
        2. Identify genuinely new jobs
        3. Match new jobs against user career profiles
        4. Create notifications for new matches

    Existing jobs are updated by ingestion but do not trigger
    new notifications.
    """

    # ============================================================
    # 1. DISCOVER AND INGEST JOBS
    # ============================================================

    source = MockJobSource()

    created_jobs, updated_jobs = ingest_jobs(
        db=db,
        source=source,
    )

    # ============================================================
    # 2. NO NEW JOBS
    # ============================================================

    if not created_jobs:
        return {
            "jobs_found": 0,
            "new_jobs": 0,
            "updated_jobs": len(updated_jobs),
            "matches_created": 0,
            "notifications_created": 0,
        }

    # ============================================================
    # 3. GET CAREER PROFILES
    # ============================================================

    profiles = (
        db.query(CareerProfile)
        .all()
    )

    matches_created = 0
    notifications_created = 0

    # ============================================================
    # 4. MATCH NEW JOBS AGAINST EVERY PROFILE
    # ============================================================

    for profile in profiles:

        for job in created_jobs:

            # ----------------------------------------------------
            # Calculate match score
            # ----------------------------------------------------

            score, reasons = calculate_match_score(
                profile=profile,
                job=job,
            )

            # ----------------------------------------------------
            # Check whether match already exists
            # ----------------------------------------------------

            from app.models.job_match import JobMatch

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
                match.match_reasons = "; ".join(
                    reasons
                )

            else:
                # ------------------------------------------------
                # Create new match
                # ------------------------------------------------

                match = JobMatch(
                    user_id=profile.user_id,
                    job_id=job.id,
                    score=score,
                    match_reasons="; ".join(
                        reasons
                    ),
                )

                db.add(match)
                db.flush()

                matches_created += 1

            # ----------------------------------------------------
            # Create notification
            # ----------------------------------------------------

            notification = create_notification_for_match(
                db=db,
                match=match,
            )

            if notification:
                notifications_created += 1

    # ============================================================
    # 5. SAVE EVERYTHING
    # ============================================================

    db.commit()

    return {
        "jobs_found": len(created_jobs),
        "new_jobs": len(created_jobs),
        "updated_jobs": len(updated_jobs),
        "matches_created": matches_created,
        "notifications_created": notifications_created,
    }