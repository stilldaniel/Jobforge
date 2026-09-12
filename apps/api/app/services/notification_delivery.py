from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationDelivery(ABC):
    """
    Base interface for notification delivery.

    Different delivery channels such as email or push
    can implement this interface.
    """

    @abstractmethod
    def send(
        self,
        db: Session,
        notification: Notification,
    ) -> bool:
        """
        Attempt to deliver a notification.

        Returns:
            True  -> delivery succeeded
            False -> delivery failed
        """
        raise NotImplementedError