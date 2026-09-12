import logging

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.notification_delivery import (
    NotificationDelivery,
)


logger = logging.getLogger(__name__)


class EmailDelivery(NotificationDelivery):
    """
    Development email delivery implementation.

    This currently simulates email delivery.
    A real email provider will be connected later.
    """

    def send(
        self,
        db: Session,
        notification: Notification,
    ) -> bool:
        logger.info(
            "EMAIL DELIVERY | notification_id=%s | "
            "user_id=%s | subject=%s | message=%s",
            notification.id,
            notification.user_id,
            notification.title,
            notification.message,
        )

        return True