import pytest
from datetime import datetime, timezone

from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.notification import Notification
from app.models.user import User
from app.services.notification_service import (
    create_notification_for_match,
    mark_notification_as_sent,
)


@pytest.fixture
def user(db):
    test_user = User(
        email="notification-test@example.com",
        full_name="Notification Test User",
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
        fingerprint="notification-test-fingerprint",
    )

    db.add(test_job)
    db.commit()
    db.refresh(test_job)

    return test_job


def create_match(
    db,
    user_id,
    job_id,
    score=95,
):
    match = JobMatch(
        user_id=user_id,
        job_id=job_id,
        score=score,
        match_reasons="Strong match based on skills and experience.",
    )

    db.add(match)
    db.commit()
    db.refresh(match)

    return match


def test_create_immediate_notification_for_high_score(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=95,
    )

    notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert notification is not None
    assert notification.user_id == user.id
    assert notification.job_match_id == match.id
    assert notification.notification_type == "immediate"
    assert notification.channel == "email"
    assert notification.status == "pending"
    assert notification.title == "New high-quality job match"
    assert notification.attempts == 0


def test_create_digest_notification_for_score_at_or_below_90(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=90,
    )

    notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert notification is not None
    assert notification.notification_type == "digest"
    assert notification.channel == "email"
    assert notification.status == "pending"
    assert notification.title == "New job match"
    assert notification.attempts == 0


def test_create_digest_notification_for_lower_score(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=70,
    )

    notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert notification is not None
    assert notification.notification_type == "digest"
    assert notification.status == "pending"


def test_notification_message_contains_job_details(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=95,
    )

    notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert notification is not None
    assert job.title in notification.message
    assert job.company in notification.message
    assert "95%" in notification.message


def test_duplicate_notification_is_not_created(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=95,
    )

    first_notification = create_notification_for_match(
        db=db,
        match=match,
    )

    second_notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert first_notification is not None
    assert second_notification is None

    notifications = (
        db.query(Notification)
        .filter(Notification.job_match_id == match.id)
        .all()
    )

    assert len(notifications) == 1


def test_duplicate_notification_is_prevented_even_after_sent(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=95,
    )

    notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert notification is not None

    mark_notification_as_sent(
        db=db,
        notification=notification,
    )

    db.commit()
    db.refresh(notification)

    duplicate = create_notification_for_match(
        db=db,
        match=match,
    )

    assert duplicate is None
    assert notification.status == "sent"
    assert notification.sent_at is not None


def test_mark_notification_as_sent(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=95,
    )

    notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert notification is not None
    assert notification.status == "pending"
    assert notification.sent_at is None

    result = mark_notification_as_sent(
        db=db,
        notification=notification,
    )

    db.commit()
    db.refresh(notification)

    assert result is notification
    assert notification.status == "sent"
    assert notification.sent_at is not None
    assert notification.last_error is None


def test_mark_notification_as_sent_clears_previous_error(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=95,
    )

    notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert notification is not None

    notification.status = "pending"
    notification.attempts = 2
    notification.last_error = "Previous delivery failure"

    db.commit()
    db.refresh(notification)

    mark_notification_as_sent(
        db=db,
        notification=notification,
    )

    db.commit()
    db.refresh(notification)

    assert notification.status == "sent"
    assert notification.last_error is None
    assert notification.sent_at is not None


def test_notification_defaults_attempts_to_zero(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=95,
    )

    notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert notification is not None
    assert notification.attempts == 0


def test_immediate_threshold_is_strictly_above_90(
    db,
    user,
    job,
):
    match_90 = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=90,
    )

    notification_90 = create_notification_for_match(
        db=db,
        match=match_90,
    )

    assert notification_90 is not None
    assert notification_90.notification_type == "digest"

    match_91 = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=91,
    )

    notification_91 = create_notification_for_match(
        db=db,
        match=match_91,
    )

    assert notification_91 is not None
    assert notification_91.notification_type == "immediate"


def test_notification_can_be_read_without_affecting_delivery_status(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=95,
    )

    notification = create_notification_for_match(
        db=db,
        match=match,
    )

    assert notification is not None

    notification.read_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notification)

    assert notification.read_at is not None
    assert notification.status == "pending"