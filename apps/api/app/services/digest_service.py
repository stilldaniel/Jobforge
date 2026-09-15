import logging

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.email_delivery import EmailDelivery
from app.services.notification_service import (
    mark_notification_as_sent,
)


logger = logging.getLogger(__name__)


def process_immediate_notifications(
    db: Session,
) -> dict:
    """
    Process pending immediate notifications only.

    Immediate notifications are sent individually as soon as
    they are created.

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
                notification.status = "failed"
                notification.last_error = (
                    "Notification delivery failed."
                )

                notifications_failed += 1

        except Exception as exc:
            notification.status = "failed"
            notification.last_error = str(exc)

            logger.exception(
                "Immediate notification delivery failed | "
                "notification_id=%s",
                notification.id,
            )

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
                notification.status = "failed"
                notification.last_error = (
                    "Notification delivery failed."
                )

                notifications_failed += 1

        except Exception as exc:
            notification.status = "failed"
            notification.last_error = str(exc)

            logger.exception(
                "Notification delivery failed | "
                "notification_id=%s",
                notification.id,
            )

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

    Example:

        User has 3 pending digest matches

        Match A
        Match B
        Match C

        ↓

        One digest email containing A, B and C.
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
            if any(
                notification.channel != "email"
                for notification in user_notifications
            ):
                unsupported_channels = sorted(
                    {
                        notification.channel
                        for notification in user_notifications
                        if notification.channel != "email"
                    }
                )

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
                notification.status = "failed"
                notification.last_error = str(exc)

                notifications_failed += 1

    db.commit()

    return {
        "users_processed": users_processed,
        "notifications_processed": notifications_processed,
        "notifications_sent": notifications_sent,
        "notifications_failed": notifications_failed,
    }