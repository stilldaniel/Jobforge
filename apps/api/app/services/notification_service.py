import logging
import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.job_match import JobMatch
from app.models.notification import Notification


logger = logging.getLogger(__name__)

# Below this score a match is still stored and shown in the app,
# but it doesn't generate a notification. Jobs that fail a hard
# eligibility check (location, salary) are capped at 49.
DEFAULT_MIN_NOTIFICATION_SCORE = 60


def get_min_notification_score() -> int:
    """
    Return the lowest match score that creates a notification.
    """

    value = os.getenv(
        "NOTIFICATION_MIN_SCORE",
        str(DEFAULT_MIN_NOTIFICATION_SCORE),
    )

    try:
        score = int(value)
    except ValueError:
        logger.warning(
            "Invalid NOTIFICATION_MIN_SCORE=%s. Falling back to %s.",
            value,
            DEFAULT_MIN_NOTIFICATION_SCORE,
        )
        return DEFAULT_MIN_NOTIFICATION_SCORE

    return max(0, min(score, 100))


def create_notification_for_match(
    db: Session,
    match: JobMatch,
) -> Notification | None:
    """
    Create a notification for a job match.

    Matches above 90 receive an immediate notification.
    Matches at or below 90 are added to the digest queue.

    A notification will not be created if the match scores below
    the minimum notification score, or if one already exists for
    this job match.
    """

    if match.score < get_min_notification_score():
        return None

    existing_notification = (
        db.query(Notification)
        .filter(Notification.job_match_id == match.id)
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
    db.flush()

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