from datetime import datetime, timezone

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

    existing_notification = (
        db.query(Notification)
        .filter(
            Notification.job_match_id == match.id
        )
        .first()
    )

    if existing_notification:
        return None

    if match.score > 90:
        notification_type = "immediate"
        title = "New high-quality job match"
    else:
        notification_type = "digest"
        title = "New job match"

    job = match.job

    message = (
        f"{job.title} at {job.company} "
        f"matches your career profile with a score of "
        f"{match.score}%."
    )

    notification = Notification(
        user_id=match.user_id,
        job_match_id=match.id,
        notification_type=notification_type,
        channel="email",
        status="pending",
        title=title,
        message=message,
        attempts=0,
        last_error=None,
    )

    db.add(notification)

    return notification


def mark_notification_as_sent(
    db: Session,
    notification: Notification,
) -> Notification:
    """
    Mark a notification as successfully sent.
    """

    notification.status = "sent"
    notification.sent_at = datetime.now(timezone.utc)
    notification.last_error = None

    return notification