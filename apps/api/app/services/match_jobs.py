from sqlalchemy.orm import Session

from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.services.matching import calculate_match_score


def generate_job_matches(
    user_id: int,
    db: Session,
) -> list[JobMatch]:
    """
    Generate or update job matches for a user based on
    their career profile.

    Existing matches are updated.
    New matches are created.

    Matches for jobs that no longer exist are removed.

    Returns:
        A list of JobMatch records sorted by highest score first.
    """

    # ============================================================
    # 1. GET USER'S CAREER PROFILE
    # ============================================================

    profile = (
        db.query(CareerProfile)
        .filter(
            CareerProfile.user_id == user_id
        )
        .first()
    )

    if not profile:
        raise ValueError(
            "Career profile not found"
        )

    # ============================================================
    # 2. GET ALL JOBS
    # ============================================================

    jobs = (
        db.query(Job)
        .order_by(Job.id.asc())
        .all()
    )

    # ============================================================
    # 3. GET EXISTING MATCHES
    # ============================================================

    existing_matches = (
        db.query(JobMatch)
        .filter(
            JobMatch.user_id == user_id
        )
        .all()
    )

    existing_matches_by_job_id = {
        match.job_id: match
        for match in existing_matches
    }

    # Keep track of jobs that actually exist.
    job_ids = {
        job.id
        for job in jobs
    }

    # ============================================================
    # 4. REMOVE STALE MATCHES
    # ============================================================
    #
    # If a job has been deleted from the jobs table, its old
    # match should no longer appear for the user.
    #

    stale_matches = [
        match
        for match in existing_matches
        if match.job_id not in job_ids
    ]

    for match in stale_matches:
        db.delete(match)

    # ============================================================
    # 5. NO JOBS AVAILABLE
    # ============================================================

    if not jobs:

        db.commit()

        return []

    # ============================================================
    # 6. GENERATE / UPDATE MATCHES
    # ============================================================

    matches: list[JobMatch] = []

    for job in jobs:

        # --------------------------------------------------------
        # Calculate the match score
        # --------------------------------------------------------

        score, reasons = calculate_match_score(
            profile=profile,
            job=job,
        )

        match_reasons = "; ".join(reasons)

        # --------------------------------------------------------
        # Check whether a match already exists
        # --------------------------------------------------------

        existing_match = (
            existing_matches_by_job_id.get(
                job.id
            )
        )

        # ========================================================
        # UPDATE EXISTING MATCH
        # ========================================================

        if existing_match:

            existing_match.score = score

            existing_match.match_reasons = (
                match_reasons
            )

            matches.append(
                existing_match
            )

        # ========================================================
        # CREATE NEW MATCH
        # ========================================================

        else:

            match = JobMatch(
                user_id=user_id,
                job_id=job.id,
                score=score,
                match_reasons=match_reasons,
            )

            db.add(match)

            matches.append(match)

    # ============================================================
    # 7. SAVE CHANGES
    # ============================================================

    db.commit()

    # ============================================================
    # 8. REFRESH MATCHES
    # ============================================================

    for match in matches:
        db.refresh(match)

    # ============================================================
    # 9. SORT BY SCORE
    # ============================================================

    matches.sort(
        key=lambda match: (
            match.score,
            match.id,
        ),
        reverse=True,
    )

    return matches