import logging
import os

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User
from app.services.email_delivery import EmailDelivery
from app.services.notification_service import (
    mark_notification_as_sent,
)


logger = logging.getLogger(__name__)


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
) -> dict:
    """
    Process pending digest notifications as aggregated emails.

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

    for user_id, user_notifications in notifications_by_user.items():
        users_processed += 1

        user = db.query(User).filter(User.id == user_id).first()

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