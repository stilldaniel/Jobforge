import html
import logging
import os

import resend
from sqlalchemy.orm import Session

from app.models.job_match import JobMatch
from app.models.notification import Notification
from app.models.user import User
from app.services.notification_delivery import NotificationDelivery


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
            .filter(User.id == notification.user_id)
            .first()
        )

        if not user:
            raise ValueError(
                f"User {notification.user_id} "
                f"not found for notification delivery."
            )

        api_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("RESEND_FROM_EMAIL")

        if not api_key:
            raise ValueError(
                "RESEND_API_KEY environment variable "
                "is not configured."
            )

        if not from_email:
            raise ValueError(
                "RESEND_FROM_EMAIL environment variable "
                "is not configured."
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

    def send_digest(
        self,
        db: Session,
        user_id: int,
        notifications: list[Notification],
    ) -> bool:
        """
        Send one aggregated digest email for a user.

        Every notification in `notifications` represents one
        pending digest job match.
        """

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise ValueError(
                f"User {user_id} not found for digest delivery."
            )

        if not notifications:
            return False

        api_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("RESEND_FROM_EMAIL")

        if not api_key:
            raise ValueError(
                "RESEND_API_KEY environment variable "
                "is not configured."
            )

        if not from_email:
            raise ValueError(
                "RESEND_FROM_EMAIL environment variable "
                "is not configured."
            )

        resend.api_key = api_key

        html_content = self._build_digest_html(
            notifications=notifications,
        )

        params = {
            "from": from_email,
            "to": [user.email],
            "subject": (
                f"JobForge — {len(notifications)} "
                f"new job match"
                f"{'es' if len(notifications) != 1 else ''}"
            ),
            "html": html_content,
        }

        email = resend.Emails.send(params)

        logger.info(
            "DIGEST EMAIL SENT | user_id=%s | "
            "recipient=%s | notifications=%s | email_id=%s",
            user_id,
            user.email,
            len(notifications),
            getattr(email, "id", None),
        )

        return True

    @staticmethod
    def _build_html(
        notification: Notification,
    ) -> str:
        message = html.escape(
            notification.message or ""
        )

        title = html.escape(
            notification.title
        )

        job = notification.job_match.job

        job_title = html.escape(
            job.title
        )

        company = html.escape(
            job.company
        )

        application_url = html.escape(
            job.application_url,
            quote=True,
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta
                name="viewport"
                content="width=device-width,
                initial-scale=1.0"
            >
            <title>{title}</title>
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
                        {title}
                    </h2>

                    <p
                        style="
                            font-size: 16px;
                            line-height: 1.6;
                        "
                    >
                        {message}
                    </p>

                    <p>
                        <strong>{job_title}</strong>
                        at {company}
                    </p>

                    <a
                        href="{application_url}"
                        style="
                            display: inline-block;
                            margin-top: 12px;
                            padding: 12px 18px;
                            background-color: #111827;
                            color: white;
                            text-decoration: none;
                            border-radius: 8px;
                        "
                    >
                        View Job
                    </a>

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

    @staticmethod
    def _build_digest_html(
        notifications: list[Notification],
    ) -> str:
        job_cards = []

        for notification in notifications:
            job_match: JobMatch = notification.job_match
            job = job_match.job

            job_title = html.escape(
                job.title
            )

            company = html.escape(
                job.company
            )

            score = job_match.score

            application_url = html.escape(
                job.application_url,
                quote=True,
            )

            match_reasons = html.escape(
                job_match.match_reasons or ""
            )

            reasons_html = ""

            if match_reasons:
                reasons_html = f"""
                    <p
                        style="
                            margin: 8px 0 0;
                            color: #6b7280;
                            font-size: 14px;
                            line-height: 1.5;
                        "
                    >
                        {match_reasons}
                    </p>
                """

            job_cards.append(
                f"""
                <div
                    style="
                        border: 1px solid #e5e7eb;
                        border-radius: 10px;
                        padding: 20px;
                        margin-bottom: 16px;
                    "
                >
                    <h3
                        style="
                            margin: 0 0 8px;
                            color: #111827;
                            font-size: 18px;
                        "
                    >
                        {job_title}
                    </h3>

                    <p
                        style="
                            margin: 0;
                            color: #4b5563;
                            font-size: 15px;
                        "
                    >
                        {company}
                    </p>

                    <p
                        style="
                            margin: 12px 0 0;
                            font-weight: bold;
                            color: #111827;
                        "
                    >
                        Match score: {score}%
                    </p>

                    {reasons_html}

                    <a
                        href="{application_url}"
                        style="
                            display: inline-block;
                            margin-top: 16px;
                            padding: 10px 16px;
                            background-color: #111827;
                            color: white;
                            text-decoration: none;
                            border-radius: 7px;
                            font-size: 14px;
                        "
                    >
                        View Job
                    </a>
                </div>
                """
            )

        jobs_html = "".join(job_cards)

        job_count = len(notifications)

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta
                name="viewport"
                content="width=device-width,
                initial-scale=1.0"
            >
            <title>JobForge Job Digest</title>
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
                    max-width: 650px;
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
                        Your Job Digest
                    </h2>

                    <p
                        style="
                            font-size: 16px;
                            line-height: 1.6;
                            color: #4b5563;
                        "
                    >
                        You have {job_count} new job
                        match{"es" if job_count != 1 else ""}.
                    </p>

                    {jobs_html}

                    <p
                        style="
                            margin-top: 32px;
                            color: #6b7280;
                            font-size: 14px;
                            line-height: 1.5;
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