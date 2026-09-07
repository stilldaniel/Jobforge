from sqlalchemy.orm import Session

from app.models.job_match import JobMatch
from app.models.notification import Notification


def create_notification_for_match(
    db: Session,
    match: JobMatch,
) -> Notification | None:
    """
    Create a notification for a job match.

    Matches above 90 receive an immediate notification.
    Matches at or below 90 are added to the digest queue.

    A notification will not be created if one already exists
    for this job match.
    """

    # --------------------------------------------------
    # CHECK FOR EXISTING NOTIFICATION
    # --------------------------------------------------

    existing_notification = (
        db.query(Notification)
        .filter(
            Notification.job_match_id == match.id
        )
        .first()
    )

    if existing_notification:
        return None

    # --------------------------------------------------
    # DETERMINE NOTIFICATION TYPE
    # --------------------------------------------------

    if match.score > 90:
        notification_type = "immediate"
        title = "New high-quality job match"
    else:
        notification_type = "digest"
        title = "New job match"

    # --------------------------------------------------
    # CREATE MESSAGE
    # --------------------------------------------------

    job = match.job

    message = (
        f"{job.title} at {job.company} "
        f"matches your career profile with a score of "
        f"{match.score}%."
    )

    # --------------------------------------------------
    # CREATE NOTIFICATION
    # --------------------------------------------------

    notification = Notification(
        user_id=match.user_id,
        job_match_id=match.id,
        notification_type=notification_type,
        status="pending",
        title=title,
        message=message,
    )

    db.add(notification)

    return notification