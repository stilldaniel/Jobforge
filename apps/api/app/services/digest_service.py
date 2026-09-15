import logging
import os

from sqlalchemy.orm import Session

from app.models.notification import Notification
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


def process_immediate_notifications(
    db: Session,
) -> dict:
    """
    Process pending immediate notifications only.

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
        }

    max_attempts = get_max_notification_attempts()

    notifications_sent = 0
    notifications_failed = 0

    for notification in notifications:
        notification.attempts += 1

        try:
            if notification.channel == "email":
                delivery = EmailDelivery()
            else:
                raise ValueError(
                    f"Unsupported notification channel: "
                    f"{notification.channel}"
                )

            delivered = delivery.send(
                db=db,
                notification=notification,
            )

            if delivered:
                mark_notification_as_sent(
                    db=db,
                    notification=notification,
                )

                notifications_sent += 1

            else:
                permanently_failed = handle_delivery_failure(
                    notification=notification,
                    error="Notification delivery failed.",
                    max_attempts=max_attempts,
                )

                if permanently_failed:
                    notifications_failed += 1

        except Exception as exc:
            permanently_failed = handle_delivery_failure(
                notification=notification,
                error=str(exc),
                max_attempts=max_attempts,
            )

            logger.exception(
                "Immediate notification delivery failed | "
                "notification_id=%s | attempt=%s/%s",
                notification.id,
                notification.attempts,
                max_attempts,
            )

            if permanently_failed:
                notifications_failed += 1

    db.commit()

    return {
        "notifications_processed": len(notifications),
        "notifications_sent": notifications_sent,
        "notifications_failed": notifications_failed,
    }


def process_pending_notifications(
    db: Session,
) -> dict:
    """
    Process all pending notifications individually.

    This is retained as a manual/legacy processor.

    The normal automated flow should use:
    - process_immediate_notifications()
    - process_digest_notifications()
    """

    notifications = (
        db.query(Notification)
        .filter(
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
        }

    max_attempts = get_max_notification_attempts()

    notifications_sent = 0
    notifications_failed = 0

    for notification in notifications:
        notification.attempts += 1

        try:
            if notification.channel == "email":
                delivery = EmailDelivery()
            else:
                raise ValueError(
                    f"Unsupported notification channel: "
                    f"{notification.channel}"
                )

            delivered = delivery.send(
                db=db,
                notification=notification,
            )

            if delivered:
                mark_notification_as_sent(
                    db=db,
                    notification=notification,
                )

                notifications_sent += 1

            else:
                permanently_failed = handle_delivery_failure(
                    notification=notification,
                    error="Notification delivery failed.",
                    max_attempts=max_attempts,
                )

                if permanently_failed:
                    notifications_failed += 1

        except Exception as exc:
            permanently_failed = handle_delivery_failure(
                notification=notification,
                error=str(exc),
                max_attempts=max_attempts,
            )

            logger.exception(
                "Notification delivery failed | "
                "notification_id=%s | attempt=%s/%s",
                notification.id,
                notification.attempts,
                max_attempts,
            )

            if permanently_failed:
                notifications_failed += 1

    db.commit()

    return {
        "notifications_processed": len(notifications),
        "notifications_sent": notifications_sent,
        "notifications_failed": notifications_failed,
    }


def process_digest_notifications(
    db: Session,
) -> dict:
    """
    Process pending digest notifications as aggregated emails.

    All pending digest notifications belonging to the same user
    are combined into a single email.

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

    delivery = EmailDelivery()

    for user_id, user_notifications in notifications_by_user.items():
        users_processed += 1

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
    }