import pytest

from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.notification import Notification
from app.models.user import User
from app.services import digest_service


@pytest.fixture
def user(db):
    test_user = User(
        email="digest-test@example.com",
        full_name="Digest Test User",
        timezone="Africa/Lagos",
    )

    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    return test_user


@pytest.fixture
def second_user(db):
    test_user = User(
        email="digest-test-2@example.com",
        full_name="Second Digest User",
        timezone="Africa/Lagos",
    )

    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    return test_user


@pytest.fixture
def job(db):
    test_job = Job(
        title="Frontend Developer",
        company="Test Company",
        description="Build modern web applications.",
        required_skills="React, Next.js, TypeScript",
        required_experience=3,
        location="Lagos, Nigeria",
        remote_eligibility="Worldwide",
        work_type="remote",
        salary_min=3000,
        salary_max=5000,
        application_url="https://example.com/jobs/frontend",
        source="test",
        fingerprint="digest-test-fingerprint",
    )

    db.add(test_job)
    db.commit()
    db.refresh(test_job)

    return test_job


def create_notification(
    db,
    user_id,
    job_id,
    notification_type="immediate",
    score=95,
    channel="email",
    status="pending",
):
    match = JobMatch(
        user_id=user_id,
        job_id=job_id,
        score=score,
        match_reasons="Strong match.",
    )

    db.add(match)
    db.commit()
    db.refresh(match)

    notification = Notification(
        user_id=user_id,
        job_match_id=match.id,
        notification_type=notification_type,
        channel=channel,
        status=status,
        title=(
            "New high-quality job match"
            if notification_type == "immediate"
            else "New job match"
        ),
        message="Test notification.",
        attempts=0,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def test_get_max_notification_attempts_defaults_to_three(
    monkeypatch,
):
    monkeypatch.delenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        raising=False,
    )

    assert digest_service.get_max_notification_attempts() == 3


def test_get_max_notification_attempts_reads_environment(
    monkeypatch,
):
    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "5",
    )

    assert digest_service.get_max_notification_attempts() == 5


def test_get_max_notification_attempts_never_returns_less_than_one(
    monkeypatch,
):
    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "0",
    )

    assert digest_service.get_max_notification_attempts() == 1


def test_get_max_notification_attempts_handles_invalid_value(
    monkeypatch,
):
    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "invalid",
    )

    assert digest_service.get_max_notification_attempts() == 3


def test_handle_delivery_failure_keeps_notification_pending_before_max_attempts(
    db,
    user,
    job,
):
    notification = create_notification(
        db,
        user.id,
        job.id,
        notification_type="immediate",
    )

    notification.attempts = 1

    permanently_failed = digest_service.handle_delivery_failure(
        notification=notification,
        error="Temporary delivery failure",
        max_attempts=3,
    )

    assert permanently_failed is False
    assert notification.status == "pending"
    assert notification.last_error == "Temporary delivery failure"


def test_handle_delivery_failure_marks_notification_failed_at_max_attempts(
    db,
    user,
    job,
):
    notification = create_notification(
        db,
        user.id,
        job.id,
        notification_type="immediate",
    )

    notification.attempts = 3

    permanently_failed = digest_service.handle_delivery_failure(
        notification=notification,
        error="Permanent delivery failure",
        max_attempts=3,
    )

    assert permanently_failed is True
    assert notification.status == "failed"
    assert notification.last_error == "Permanent delivery failure"


def test_immediate_notification_is_sent_successfully(
    db,
    user,
    job,
    monkeypatch,
):
    notification = create_notification(
        db,
        user.id,
        job.id,
        notification_type="immediate",
    )

    class FakeEmailDelivery:
        def send(self, db, notification):
            return True

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    result = digest_service.process_immediate_notifications(
        db=db,
    )

    db.refresh(notification)

    assert result == {
        "notifications_processed": 1,
        "notifications_sent": 1,
        "notifications_failed": 0,
    }

    assert notification.status == "sent"
    assert notification.attempts == 1
    assert notification.sent_at is not None
    assert notification.last_error is None


def test_immediate_notification_failure_remains_pending(
    db,
    user,
    job,
    monkeypatch,
):
    notification = create_notification(
        db,
        user.id,
        job.id,
        notification_type="immediate",
    )

    class FakeEmailDelivery:
        def send(self, db, notification):
            return False

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "3",
    )

    result = digest_service.process_immediate_notifications(
        db=db,
    )

    db.refresh(notification)

    assert result == {
        "notifications_processed": 1,
        "notifications_sent": 0,
        "notifications_failed": 0,
    }

    assert notification.status == "pending"
    assert notification.attempts == 1
    assert notification.sent_at is None
    assert notification.last_error == "Notification delivery failed."


def test_immediate_notification_exception_remains_pending(
    db,
    user,
    job,
    monkeypatch,
):
    notification = create_notification(
        db,
        user.id,
        job.id,
        notification_type="immediate",
    )

    class FakeEmailDelivery:
        def send(self, db, notification):
            raise RuntimeError(
                "Email provider unavailable"
            )

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "3",
    )

    result = digest_service.process_immediate_notifications(
        db=db,
    )

    db.refresh(notification)

    assert result == {
        "notifications_processed": 1,
        "notifications_sent": 0,
        "notifications_failed": 0,
    }

    assert notification.status == "pending"
    assert notification.attempts == 1
    assert notification.last_error == "Email provider unavailable"


def test_immediate_notification_fails_after_max_attempts(
    db,
    user,
    job,
    monkeypatch,
):
    notification = create_notification(
        db,
        user.id,
        job.id,
        notification_type="immediate",
    )

    class FakeEmailDelivery:
        def send(self, db, notification):
            raise RuntimeError(
                "Email provider unavailable"
            )

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "3",
    )

    digest_service.process_immediate_notifications(db=db)

    db.refresh(notification)

    assert notification.status == "pending"
    assert notification.attempts == 1

    digest_service.process_immediate_notifications(db=db)

    db.refresh(notification)

    assert notification.status == "pending"
    assert notification.attempts == 2

    result = digest_service.process_immediate_notifications(
        db=db,
    )

    db.refresh(notification)

    assert result == {
        "notifications_processed": 1,
        "notifications_sent": 0,
        "notifications_failed": 1,
    }

    assert notification.status == "failed"
    assert notification.attempts == 3
    assert notification.last_error == "Email provider unavailable"


def test_unsupported_immediate_channel_retries(
    db,
    user,
    job,
    monkeypatch,
):
    notification = create_notification(
        db,
        user.id,
        job.id,
        notification_type="immediate",
        channel="sms",
    )

    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "3",
    )

    result = digest_service.process_immediate_notifications(
        db=db,
    )

    db.refresh(notification)

    assert result == {
        "notifications_processed": 1,
        "notifications_sent": 0,
        "notifications_failed": 0,
    }

    assert notification.status == "pending"
    assert notification.attempts == 1
    assert (
        notification.last_error
        == "Unsupported notification channel: sms"
    )


def test_no_pending_immediate_notifications_returns_zero_counts(
    db,
):
    result = digest_service.process_immediate_notifications(
        db=db,
    )

    assert result == {
        "notifications_processed": 0,
        "notifications_sent": 0,
        "notifications_failed": 0,
    }


def test_digest_notifications_for_same_user_are_aggregated(
    db,
    user,
    job,
    monkeypatch,
):
    first = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
        score=80,
    )

    second = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
        score=75,
    )

    captured = {}

    class FakeEmailDelivery:
        def send_digest(
            self,
            db,
            user_id,
            notifications,
        ):
            captured["user_id"] = user_id
            captured["notifications"] = notifications

            return True

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    result = digest_service.process_digest_notifications(
        db=db,
    )

    db.refresh(first)
    db.refresh(second)

    assert result == {
        "users_processed": 1,
        "notifications_processed": 2,
        "notifications_sent": 2,
        "notifications_failed": 0,
    }

    assert captured["user_id"] == user.id
    assert len(captured["notifications"]) == 2

    assert first.status == "sent"
    assert second.status == "sent"

    assert first.attempts == 1
    assert second.attempts == 1

    assert first.sent_at is not None
    assert second.sent_at is not None


def test_digest_notifications_are_grouped_by_user(
    db,
    user,
    second_user,
    job,
    monkeypatch,
):
    first = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
        score=80,
    )

    second = create_notification(
        db,
        second_user.id,
        job.id,
        notification_type="digest",
        score=70,
    )

    captured = []

    class FakeEmailDelivery:
        def send_digest(
            self,
            db,
            user_id,
            notifications,
        ):
            captured.append(
                {
                    "user_id": user_id,
                    "notification_count": len(
                        notifications
                    ),
                }
            )

            return True

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    result = digest_service.process_digest_notifications(
        db=db,
    )

    db.refresh(first)
    db.refresh(second)

    assert result == {
        "users_processed": 2,
        "notifications_processed": 2,
        "notifications_sent": 2,
        "notifications_failed": 0,
    }

    assert len(captured) == 2

    captured_by_user = {
        item["user_id"]: item["notification_count"]
        for item in captured
    }

    assert captured_by_user[user.id] == 1
    assert captured_by_user[second_user.id] == 1

    assert first.status == "sent"
    assert second.status == "sent"


def test_digest_failure_keeps_notifications_pending(
    db,
    user,
    job,
    monkeypatch,
):
    first = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
    )

    second = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
    )

    class FakeEmailDelivery:
        def send_digest(
            self,
            db,
            user_id,
            notifications,
        ):
            raise RuntimeError(
                "Digest provider unavailable"
            )

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "3",
    )

    result = digest_service.process_digest_notifications(
        db=db,
    )

    db.refresh(first)
    db.refresh(second)

    assert result == {
        "users_processed": 1,
        "notifications_processed": 0,
        "notifications_sent": 0,
        "notifications_failed": 0,
    }

    assert first.status == "pending"
    assert second.status == "pending"

    assert first.attempts == 1
    assert second.attempts == 1

    assert first.last_error == "Digest provider unavailable"
    assert second.last_error == "Digest provider unavailable"


def test_digest_failure_marks_all_notifications_failed_after_max_attempts(
    db,
    user,
    job,
    monkeypatch,
):
    first = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
    )

    second = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
    )

    class FakeEmailDelivery:
        def send_digest(
            self,
            db,
            user_id,
            notifications,
        ):
            raise RuntimeError(
                "Digest provider unavailable"
            )

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "3",
    )

    digest_service.process_digest_notifications(db=db)
    digest_service.process_digest_notifications(db=db)

    result = digest_service.process_digest_notifications(
        db=db,
    )

    db.refresh(first)
    db.refresh(second)

    assert result == {
        "users_processed": 1,
        "notifications_processed": 0,
        "notifications_sent": 0,
        "notifications_failed": 2,
    }

    assert first.status == "failed"
    assert second.status == "failed"

    assert first.attempts == 3
    assert second.attempts == 3

    assert first.last_error == "Digest provider unavailable"
    assert second.last_error == "Digest provider unavailable"


def test_unsupported_digest_channel_keeps_group_pending(
    db,
    user,
    job,
    monkeypatch,
):
    notification = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
        channel="sms",
    )

    monkeypatch.setenv(
        "NOTIFICATION_MAX_ATTEMPTS",
        "3",
    )

    result = digest_service.process_digest_notifications(
        db=db,
    )

    db.refresh(notification)

    assert result == {
        "users_processed": 1,
        "notifications_processed": 0,
        "notifications_sent": 0,
        "notifications_failed": 0,
    }

    assert notification.status == "pending"
    assert notification.attempts == 1

    assert (
        notification.last_error
        == "Unsupported notification channel(s): sms"
    )


def test_digest_does_not_process_immediate_notifications(
    db,
    user,
    job,
    monkeypatch,
):
    immediate = create_notification(
        db,
        user.id,
        job.id,
        notification_type="immediate",
        score=95,
    )

    digest = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
        score=80,
    )

    captured = []

    class FakeEmailDelivery:
        def send_digest(
            self,
            db,
            user_id,
            notifications,
        ):
            captured.extend(notifications)
            return True

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    digest_service.process_digest_notifications(
        db=db,
    )

    db.refresh(immediate)
    db.refresh(digest)

    assert immediate.status == "pending"
    assert immediate.attempts == 0

    assert digest.status == "sent"
    assert digest.attempts == 1

    assert len(captured) == 1
    assert captured[0].id == digest.id


def test_immediate_processor_does_not_process_digest_notifications(
    db,
    user,
    job,
    monkeypatch,
):
    immediate = create_notification(
        db,
        user.id,
        job.id,
        notification_type="immediate",
        score=95,
    )

    digest = create_notification(
        db,
        user.id,
        job.id,
        notification_type="digest",
        score=80,
    )

    class FakeEmailDelivery:
        def send(self, db, notification):
            return True

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        FakeEmailDelivery,
    )

    digest_service.process_immediate_notifications(
        db=db,
    )

    db.refresh(immediate)
    db.refresh(digest)

    assert immediate.status == "sent"
    assert immediate.attempts == 1

    assert digest.status == "pending"
    assert digest.attempts == 0