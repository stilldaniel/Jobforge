import logging
import os

import resend
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User
from app.services.notification_delivery import (
    NotificationDelivery,
)


logger = logging.getLogger(__name__)


class EmailDelivery(NotificationDelivery):
    """
    Sends notifications through Resend.
    """

    def send(
        self,
        db: Session,
        notification: Notification,
    ) -> bool:
        user = (
            db.query(User)
            .filter(
                User.id == notification.user_id
            )
            .first()
        )

        if not user:
            raise ValueError(
                f"User {notification.user_id} "
                "not found for notification delivery."
            )

        api_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("RESEND_FROM_EMAIL")

        if not api_key:
            raise ValueError(
                "RESEND_API_KEY environment variable is not configured."
            )

        if not from_email:
            raise ValueError(
                "RESEND_FROM_EMAIL environment variable is not configured."
            )

        resend.api_key = api_key

        params = {
            "from": from_email,
            "to": [user.email],
            "subject": notification.title,
            "html": self._build_html(
                notification=notification,
            ),
        }

        email = resend.Emails.send(params)

        logger.info(
            "EMAIL SENT | notification_id=%s | "
            "user_id=%s | recipient=%s | email_id=%s",
            notification.id,
            notification.user_id,
            user.email,
            getattr(email, "id", None),
        )

        return True

    @staticmethod
    def _build_html(
        notification: Notification,
    ) -> str:
        message = notification.message or ""

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1.0">
            <title>{notification.title}</title>
        </head>

        <body
            style="
                margin: 0;
                padding: 0;
                background-color: #f5f7fb;
                font-family: Arial, sans-serif;
                color: #1f2937;
            "
        >
            <div
                style="
                    max-width: 600px;
                    margin: 40px auto;
                    padding: 24px;
                "
            >
                <div
                    style="
                        background: white;
                        border-radius: 12px;
                        padding: 32px;
                        box-shadow:
                            0 2px 8px
                            rgba(0, 0, 0, 0.06);
                    "
                >
                    <h1
                        style="
                            margin-top: 0;
                            color: #111827;
                            font-size: 24px;
                        "
                    >
                        JobForge
                    </h1>

                    <h2
                        style="
                            color: #111827;
                            font-size: 20px;
                        "
                    >
                        {notification.title}
                    </h2>

                    <p
                        style="
                            font-size: 16px;
                            line-height: 1.6;
                        "
                    >
                        {message}
                    </p>

                    <p
                        style="
                            margin-top: 32px;
                            color: #6b7280;
                            font-size: 14px;
                        "
                    >
                        JobForge — helping you discover
                        opportunities that match your career.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """