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
    Generate job matches for a user based on their career profile.
    """

    # Find the user's career profile
    profile = (
        db.query(CareerProfile)
        .filter(CareerProfile.user_id == user_id)
        .first()
    )

    if not profile:
        raise ValueError("Career profile not found")

    # Get all available jobs
    jobs = db.query(Job).all()

    matches: list[JobMatch] = []

    for job in jobs:
        score, reasons = calculate_match_score(
            profile,
            job,
        )

        # Check whether this match already exists
        existing_match = (
            db.query(JobMatch)
            .filter(
                JobMatch.user_id == user_id,
                JobMatch.job_id == job.id,
            )
            .first()
        )

        if existing_match:
            # Update the existing match
            existing_match.score = score
            existing_match.match_reasons = "; ".join(reasons)

            matches.append(existing_match)

        else:
            # Create a new match
            match = JobMatch(
                user_id=user_id,
                job_id=job.id,
                score=score,
                match_reasons="; ".join(reasons),
            )

            db.add(match)
            matches.append(match)

    db.commit()

    for match in matches:
        db.refresh(match)

    return matches