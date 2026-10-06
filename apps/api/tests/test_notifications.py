import pytest
from datetime import datetime, timezone

from app.models.career_profile import CareerProfile
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

    db.add(
        CareerProfile(
            user_id=test_user.id,
            professional_title="Frontend Developer",
            skills='["React", "TypeScript"]',
            years_of_experience=3,
        )
    )
    db.commit()

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


def test_create_digest_notification_for_score_below_89(
    db,
    user,
    job,
):
    match = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=88,
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


def test_immediate_threshold_starts_at_89(
    db,
    user,
    job,
):
    match_88 = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=88,
    )

    notification_88 = create_notification_for_match(
        db=db,
        match=match_88,
    )

    assert notification_88 is not None
    assert notification_88.notification_type == "digest"

    match_89 = create_match(
        db=db,
        user_id=user.id,
        job_id=job.id,
        score=89,
    )

    notification_89 = create_notification_for_match(
        db=db,
        match=match_89,
    )

    assert notification_89 is not None
    assert notification_89.notification_type == "immediate"


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

def test_min_notification_score_defaults_to_60(monkeypatch):
    from app.services.notification_service import get_min_notification_score

    monkeypatch.delenv("NOTIFICATION_MIN_SCORE", raising=False)

    assert get_min_notification_score() == 60


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("75", 75),
        ("-5", 0),
        ("150", 100),
        ("high", 60),
    ],
)
def test_min_notification_score_configuration(
    monkeypatch,
    value,
    expected,
):
    from app.services.notification_service import get_min_notification_score

    monkeypatch.setenv("NOTIFICATION_MIN_SCORE", value)

    assert get_min_notification_score() == expected


def test_no_notification_without_career_profile(db, job):
    profileless_user = User(
        email="no-profile@example.com",
        timezone="UTC",
    )
    db.add(profileless_user)
    db.commit()

    match = create_match(
        db=db,
        user_id=profileless_user.id,
        job_id=job.id,
    )

    assert create_notification_for_match(db=db, match=match) is None


def test_no_notification_for_job_outside_candidate_field(db, user):
    sales_job = Job(
        title="Account Executive",
        company="Sales Co",
        description="Close deals. 2+ years of experience.",
        required_skills="[]",
        required_experience=2,
        location="Remote",
        remote_eligibility="Worldwide",
        work_type="remote",
        application_url="https://example.com/jobs/sales",
        source="test",
        fingerprint="sales-job-fingerprint",
    )
    db.add(sales_job)
    db.commit()

    match = create_match(
        db=db,
        user_id=user.id,
        job_id=sales_job.id,
        score=95,
    )

    assert create_notification_for_match(db=db, match=match) is None


def test_notification_when_only_skills_overlap(db, user):
    react_job = Job(
        title="Software Engineer",
        company="Product Co",
        description="Build product features.",
        required_skills='["React", "Python"]',
        location="Remote",
        remote_eligibility="Worldwide",
        work_type="remote",
        application_url="https://example.com/jobs/swe",
        source="test",
        fingerprint="skill-overlap-fingerprint",
    )
    db.add(react_job)
    db.commit()

    match = create_match(
        db=db,
        user_id=user.id,
        job_id=react_job.id,
        score=75,
    )

    assert create_notification_for_match(db=db, match=match) is not None


def test_no_notification_when_job_alerts_off(db, user, job):
    user.job_alerts_enabled = False
    db.commit()

    match = create_match(db=db, user_id=user.id, job_id=job.id, score=95)

    assert create_notification_for_match(db=db, match=match) is None


def test_high_match_goes_to_digest_when_high_match_alerts_off(
    db,
    user,
    job,
):
    user.high_match_alerts_enabled = False
    db.commit()

    match = create_match(db=db, user_id=user.id, job_id=job.id, score=95)

    notification = create_notification_for_match(db=db, match=match)

    assert notification is not None
    assert notification.notification_type == "digest"
