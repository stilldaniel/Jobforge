import logging

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.email_delivery import EmailDelivery
from app.services.notification_service import (
    mark_notification_as_sent,
)


logger = logging.getLogger(__name__)


def process_pending_notifications(
    db: Session,
) -> dict:
    """
    Process all pending notifications.

    Each notification is sent through its configured
    delivery channel.

    Failed deliveries record the attempt and error.
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
    Backwards-compatible digest processor.

    Only pending digest notifications are processed.
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

    for user_id, user_notifications in notifications_by_user.items():

        users_processed += 1

        for notification in user_notifications:

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

                    notifications_processed += 1

                else:
                    notification.status = "failed"
                    notification.last_error = (
                        "Notification delivery failed."
                    )

            except Exception as exc:

                notification.status = "failed"
                notification.last_error = str(exc)

                logger.exception(
                    "Digest notification delivery failed | "
                    "notification_id=%s",
                    notification.id,
                )

    db.commit()

    return {
        "users_processed": users_processed,
        "notifications_processed": notifications_processed,
    }