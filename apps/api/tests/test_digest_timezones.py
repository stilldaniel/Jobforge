from datetime import datetime, timezone

import pytest

from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.notification import Notification
from app.models.user import User
from app.services import digest_service


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


# The last digest went out the evening before the test times below,
# after every timezone's 08:00 (and 18:30 Lagos) on 6 October. A user
# whose last digest is older than their latest digest time gets a
# catch-up digest straight away.
YESTERDAY_EVENING = utc(2026, 10, 6, 18, 0)


class RecordingDigestDelivery:
    sent_to: list = []

    def send_digest(self, db, user_id, notifications):
        RecordingDigestDelivery.sent_to.append(user_id)
        return True


@pytest.fixture(autouse=True)
def recording_delivery(monkeypatch):
    RecordingDigestDelivery.sent_to = []

    monkeypatch.setattr(
        digest_service,
        "EmailDelivery",
        RecordingDigestDelivery,
    )
    monkeypatch.setenv("DIGEST_HOUR", "8")
    monkeypatch.setenv("DIGEST_MINUTE", "0")

    return RecordingDigestDelivery


@pytest.fixture
def job(db):
    test_job = Job(
        title="Frontend Developer",
        company="Test Company",
        application_url="https://example.com/jobs/frontend",
        source="test",
        fingerprint="timezone-digest-fingerprint",
    )

    db.add(test_job)
    db.commit()

    return test_job


def make_user(db, email, user_timezone, last_digest_at=YESTERDAY_EVENING):
    user = User(
        email=email,
        timezone=user_timezone,
        last_digest_at=last_digest_at,
    )

    db.add(user)
    db.commit()

    return user


def add_pending_digest(db, user, job):
    match = JobMatch(user_id=user.id, job_id=job.id, score=75)
    db.add(match)
    db.flush()

    db.add(
        Notification(
            user_id=user.id,
            job_match_id=match.id,
            notification_type="digest",
            channel="email",
            status="pending",
            title="New job match",
            attempts=0,
        )
    )
    db.commit()


def run_due(db, now):
    return digest_service.process_digest_notifications(
        db=db,
        now=now,
        only_due=True,
    )


def test_digest_waits_for_8am_in_the_users_timezone(db, job):
    # Africa/Lagos is UTC+1, so 08:00 local is 07:00 UTC.
    user = make_user(db, "lagos@example.com", "Africa/Lagos")
    add_pending_digest(db, user, job)

    run_due(db, utc(2026, 10, 7, 6, 45))
    assert RecordingDigestDelivery.sent_to == []

    run_due(db, utc(2026, 10, 7, 7, 0))
    assert RecordingDigestDelivery.sent_to == [user.id]


def test_users_in_different_timezones_get_digests_at_their_own_8am(db, job):
    lagos = make_user(db, "lagos@example.com", "Africa/Lagos")
    new_york = make_user(db, "ny@example.com", "America/New_York")
    add_pending_digest(db, lagos, job)
    add_pending_digest(db, new_york, job)

    # 07:00 UTC: 08:00 in Lagos, 03:00 in New York (UTC-4 in October).
    run_due(db, utc(2026, 10, 7, 7, 0))
    assert RecordingDigestDelivery.sent_to == [lagos.id]

    # 12:00 UTC: 08:00 in New York.
    run_due(db, utc(2026, 10, 7, 12, 0))
    assert RecordingDigestDelivery.sent_to == [lagos.id, new_york.id]


def test_digest_is_sent_at_most_once_a_day(db, job):
    user = make_user(db, "lagos@example.com", "Africa/Lagos")
    add_pending_digest(db, user, job)

    run_due(db, utc(2026, 10, 7, 7, 0))

    # New matches later the same day wait for tomorrow's digest.
    add_pending_digest(db, user, job)
    run_due(db, utc(2026, 10, 7, 15, 0))
    assert RecordingDigestDelivery.sent_to == [user.id]

    run_due(db, utc(2026, 10, 8, 7, 0))
    assert RecordingDigestDelivery.sent_to == [user.id, user.id]


def test_new_user_waits_for_their_next_digest_time(db, job):
    # Signed up at 15:00 Lagos time, after today's 08:00.
    user = make_user(
        db,
        "new@example.com",
        "Africa/Lagos",
        last_digest_at=None,
    )
    user.created_at = utc(2026, 10, 7, 14, 0)
    db.commit()

    add_pending_digest(db, user, job)

    run_due(db, utc(2026, 10, 7, 14, 15))
    assert RecordingDigestDelivery.sent_to == []

    run_due(db, utc(2026, 10, 8, 7, 0))
    assert RecordingDigestDelivery.sent_to == [user.id]


def test_invalid_timezone_falls_back_to_utc(db, job):
    user = make_user(db, "typo@example.com", "Lagos")
    add_pending_digest(db, user, job)

    run_due(db, utc(2026, 10, 7, 7, 45))
    assert RecordingDigestDelivery.sent_to == []

    run_due(db, utc(2026, 10, 7, 8, 0))
    assert RecordingDigestDelivery.sent_to == [user.id]


def test_digest_time_comes_from_settings(db, job, monkeypatch):
    monkeypatch.setenv("DIGEST_HOUR", "18")
    monkeypatch.setenv("DIGEST_MINUTE", "30")

    user = make_user(db, "lagos@example.com", "Africa/Lagos")
    add_pending_digest(db, user, job)

    run_due(db, utc(2026, 10, 7, 17, 15))
    assert RecordingDigestDelivery.sent_to == []

    # 18:30 Lagos is 17:30 UTC.
    run_due(db, utc(2026, 10, 7, 17, 30))
    assert RecordingDigestDelivery.sent_to == [user.id]


def test_skipped_digest_still_counts_as_todays_digest(db, job):
    user = make_user(db, "lagos@example.com", "Africa/Lagos")
    user.digest_notifications_enabled = False
    db.commit()

    add_pending_digest(db, user, job)
    run_due(db, utc(2026, 10, 7, 7, 0))

    db.refresh(user)

    assert RecordingDigestDelivery.sent_to == []
    assert user.last_digest_at is not None


def test_manual_processing_ignores_the_schedule(db, job):
    user = make_user(
        db,
        "lagos@example.com",
        "Africa/Lagos",
        last_digest_at=utc(2026, 10, 7, 7, 0),
    )
    add_pending_digest(db, user, job)

    digest_service.process_digest_notifications(
        db=db,
        now=utc(2026, 10, 7, 9, 0),
    )

    assert RecordingDigestDelivery.sent_to == [user.id]


def test_missed_digest_is_caught_up(db, job):
    # Server was down at 08:00 Lagos yesterday and today.
    user = make_user(
        db,
        "lagos@example.com",
        "Africa/Lagos",
        last_digest_at=utc(2026, 10, 5, 7, 0),
    )
    add_pending_digest(db, user, job)

    run_due(db, utc(2026, 10, 7, 6, 45))

    assert RecordingDigestDelivery.sent_to == [user.id]
