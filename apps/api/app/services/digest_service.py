import logging
import os
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User
from app.services.email_delivery import EmailDelivery
from app.services.notification_service import (
    mark_notification_as_sent,
)


logger = logging.getLogger(__name__)


def get_digest_schedule() -> tuple[int, int]:
    """
    Read and validate the daily digest schedule from environment variables.

    The time is local to each user. Defaults to 08:00 if the configured
    hour or minute is invalid.
    """

    default_hour = 8
    default_minute = 0

    try:
        hour = int(os.getenv("DIGEST_HOUR", str(default_hour)))
        minute = int(os.getenv("DIGEST_MINUTE", str(default_minute)))
    except ValueError:
        logger.warning(
            "Invalid digest schedule configuration. "
            "Falling back to 08:00."
        )
        return default_hour, default_minute

    if not 0 <= hour <= 23:
        logger.warning(
            "Invalid DIGEST_HOUR=%s. Falling back to 08:00.",
            hour,
        )
        return default_hour, default_minute

    if not 0 <= minute <= 59:
        logger.warning(
            "Invalid DIGEST_MINUTE=%s. Falling back to 08:00.",
            minute,
        )
        return default_hour, default_minute

    return hour, minute


def get_user_timezone(user: User) -> ZoneInfo:
    """
    The user's timezone, or UTC if it isn't a valid IANA name.
    """

    try:
        return ZoneInfo(user.timezone)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        logger.warning(
            "Invalid timezone %r for user_id=%s. Using UTC.",
            user.timezone,
            user.id,
        )
        return ZoneInfo("UTC")


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes; they are stored in UTC.
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


def latest_digest_time(
    user: User,
    now: datetime,
) -> datetime:
    """
    The most recent digest time (e.g. 08:00) in the user's timezone
    that is at or before `now`.
    """

    user_timezone = get_user_timezone(user)
    hour, minute = get_digest_schedule()

    local_now = now.astimezone(user_timezone)
    scheduled = datetime.combine(
        local_now.date(),
        time(hour, minute),
        tzinfo=user_timezone,
    )

    if scheduled > local_now:
        scheduled = datetime.combine(
            local_now.date() - timedelta(days=1),
            time(hour, minute),
            tzinfo=user_timezone,
        )

    return scheduled


def is_digest_due(
    user: User,
    now: datetime,
) -> bool:
    """
    Whether the user's digest time has passed since their last digest.

    A new user's first digest waits for their next digest time rather
    than going out as soon as they have a match.
    """

    last_digest_at = user.last_digest_at or user.created_at

    if last_digest_at is None:
        return True

    return _as_utc(last_digest_at) < latest_digest_time(user, now)


def get_max_notification_attempts() -> int:
    """
    Return the maximum number of delivery attempts allowed
    for a notification.
    """

    try:
        value = int(
            os.getenv(
                "NOTIFICATION_MAX_ATTEMPTS",
                "3",
            )
        )

        return max(value, 1)

    except ValueError:
        logger.warning(
            "Invalid NOTIFICATION_MAX_ATTEMPTS value. "
            "Falling back to 3."
        )

        return 3


def mark_notification_as_failed(
    notification: Notification,
    error: str,
) -> None:
    """
    Mark a notification as permanently failed.
    """

    notification.status = "failed"
    notification.last_error = error


def handle_delivery_failure(
    notification: Notification,
    error: str,
    max_attempts: int,
) -> bool:
    """
    Handle a failed notification delivery.

    Returns True when the notification has reached the
    maximum number of attempts and is permanently failed.

    Returns False when the notification should remain pending
    for another retry.
    """

    notification.last_error = error

    if notification.attempts >= max_attempts:
        mark_notification_as_failed(
            notification=notification,
            error=error,
        )

        return True

    notification.status = "pending"

    return False


def mark_notification_as_skipped(
    notification: Notification,
) -> None:
    """
    Mark a notification as not emailed because of the user's
    preferences. It still appears in the app.
    """

    notification.status = "skipped"
    notification.last_error = None


def _group_by_user(
    notifications: list[Notification],
) -> dict[int, list[Notification]]:
    notifications_by_user: dict[int, list[Notification]] = {}

    for notification in notifications:
        notifications_by_user.setdefault(
            notification.user_id,
            [],
        ).append(notification)

    return notifications_by_user


def _unsupported_channel_error(
    notifications: list[Notification],
) -> str | None:
    unsupported_channels = sorted(
        {
            notification.channel
            for notification in notifications
            if notification.channel != "email"
        }
    )

    if not unsupported_channels:
        return None

    return (
        "Unsupported notification channel: "
        + ", ".join(unsupported_channels)
    )


def process_immediate_notifications(
    db: Session,
) -> dict:
    """
    Process pending immediate notifications only.

    All of a user's pending immediate notifications are sent together:
    a single match uses the single-job email, several matches found in
    the same cycle share one email.

    User preferences are checked at send time, so changes made after a
    match was found still apply:
        - high-match alerts off: the matches move to the daily digest
        - email notifications off: nothing is emailed (still in-app)

    Failed notifications remain pending until they reach
    the maximum number of delivery attempts.

    Digest notifications are intentionally left untouched.
    """

    notifications = (
        db.query(Notification)
        .filter(
            Notification.notification_type == "immediate",
            Notification.status == "pending",
        )
        .order_by(
            Notification.created_at.asc()
        )
        .all()
    )

    if not notifications:
        return {
            "notifications_processed": 0,
            "notifications_sent": 0,
            "notifications_failed": 0,
            "notifications_skipped": 0,
        }

    max_attempts = get_max_notification_attempts()

    notifications_processed = 0
    notifications_sent = 0
    notifications_failed = 0
    notifications_skipped = 0

    delivery: EmailDelivery | None = None

    for user_id, user_notifications in _group_by_user(
        notifications
    ).items():
        user = db.query(User).filter(User.id == user_id).first()

        if user and not user.high_match_alerts_enabled:
            for notification in user_notifications:
                notification.notification_type = "digest"

            continue

        notifications_processed += len(user_notifications)

        if user and not user.email_notifications_enabled:
            for notification in user_notifications:
                mark_notification_as_skipped(notification)

            notifications_skipped += len(user_notifications)
            continue

        for notification in user_notifications:
            notification.attempts += 1

        try:
            channel_error = _unsupported_channel_error(
                user_notifications
            )

            if channel_error:
                raise ValueError(channel_error)

            if delivery is None:
                delivery = EmailDelivery()

            if len(user_notifications) == 1:
                delivered = delivery.send(
                    db=db,
                    notification=user_notifications[0],
                )
            else:
                delivered = delivery.send_high_match_batch(
                    db=db,
                    user_id=user_id,
                    notifications=user_notifications,
                )

            error = None if delivered else "Notification delivery failed."

        except Exception as exc:
            logger.exception(
                "Immediate notification delivery failed | "
                "user_id=%s | notifications=%s",
                user_id,
                len(user_notifications),
            )

            error = str(exc)

        for notification in user_notifications:
            if error is None:
                mark_notification_as_sent(
                    db=db,
                    notification=notification,
                )
                notifications_sent += 1
                continue

            permanently_failed = handle_delivery_failure(
                notification=notification,
                error=error,
                max_attempts=max_attempts,
            )

            if permanently_failed:
                notifications_failed += 1

    db.commit()

    return {
        "notifications_processed": notifications_processed,
        "notifications_sent": notifications_sent,
        "notifications_failed": notifications_failed,
        "notifications_skipped": notifications_skipped,
    }


def process_digest_notifications(
    db: Session,
    now: datetime | None = None,
    only_due: bool = False,
) -> dict:
    """
    Process pending digest notifications as aggregated emails.

    With `only_due` (the scheduler), a user is processed only once their
    digest time has passed in their own timezone, at most once a day.
    Without it (the manual endpoint), every pending digest is processed.

    All pending digest notifications belonging to the same user
    are combined into a single email.

    Users who turned off the daily digest or email notifications are
    skipped; their notifications stay visible in the app.

    Failed digest notifications remain pending until the group
    reaches the maximum number of delivery attempts.
    """

    notifications = (
        db.query(Notification)
        .filter(
            Notification.notification_type == "digest",
            Notification.status == "pending",
        )
        .order_by(
            Notification.created_at.asc()
        )
        .all()
    )

    if not notifications:
        return {
            "users_processed": 0,
            "notifications_processed": 0,
            "notifications_sent": 0,
            "notifications_failed": 0,
            "notifications_skipped": 0,
        }

    notifications_by_user: dict[
        int,
        list[Notification],
    ] = {}

    for notification in notifications:
        notifications_by_user.setdefault(
            notification.user_id,
            [],
        ).append(notification)

    max_attempts = get_max_notification_attempts()

    users_processed = 0
    notifications_processed = 0
    notifications_sent = 0
    notifications_failed = 0
    notifications_skipped = 0

    delivery = EmailDelivery()

    if now is None:
        now = datetime.now(timezone.utc)

    for user_id, user_notifications in notifications_by_user.items():
        user = db.query(User).filter(User.id == user_id).first()

        if only_due and user and not is_digest_due(user, now):
            continue

        users_processed += 1

        if user:
            user.last_digest_at = now

        if user and not (
            user.digest_notifications_enabled
            and user.email_notifications_enabled
        ):
            for notification in user_notifications:
                mark_notification_as_skipped(notification)

            notifications_processed += len(user_notifications)
            notifications_skipped += len(user_notifications)
            continue

        for notification in user_notifications:
            notification.attempts += 1

        try:
            unsupported_channels = sorted(
                {
                    notification.channel
                    for notification in user_notifications
                    if notification.channel != "email"
                }
            )

            if unsupported_channels:
                raise ValueError(
                    "Unsupported notification channel(s): "
                    + ", ".join(unsupported_channels)
                )

            delivered = delivery.send_digest(
                db=db,
                user_id=user_id,
                notifications=user_notifications,
            )

            if not delivered:
                raise ValueError(
                    "Digest email delivery failed."
                )

            for notification in user_notifications:
                mark_notification_as_sent(
                    db=db,
                    notification=notification,
                )

                notifications_processed += 1
                notifications_sent += 1

        except Exception as exc:
            logger.exception(
                "Digest email delivery failed | "
                "user_id=%s",
                user_id,
            )

            for notification in user_notifications:
                permanently_failed = handle_delivery_failure(
                    notification=notification,
                    error=str(exc),
                    max_attempts=max_attempts,
                )

                if permanently_failed:
                    notifications_failed += 1

    db.commit()

    return {
        "users_processed": users_processed,
        "notifications_processed": notifications_processed,
        "notifications_sent": notifications_sent,
        "notifications_failed": notifications_failed,
        "notifications_skipped": notifications_skipped,
    }