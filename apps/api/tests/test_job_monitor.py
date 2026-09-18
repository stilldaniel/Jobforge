from app.models.career_profile import CareerProfile
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.notification import Notification
from app.services.job_monitor import monitor_jobs
from app.job_sources.mock import MockJobSource


def make_profile(db, **overrides):
    data = {
        "user_id": None,
        "professional_title": "Frontend Developer",
        "skills": "React, Next.js, TypeScript, JavaScript, HTML, CSS, Tailwind CSS, Git",
        "years_of_experience": 5,
        "summary": "Frontend developer experienced in modern web applications.",
        "candidate_location": "Lagos, Nigeria",
        "preferred_work_type": "remote",
        "preferred_location": "Worldwide",
        "minimum_salary": 2500,
        "maximum_salary": 5000,
    }

    data.update(overrides)

    profile = CareerProfile(**data)
    db.add(profile)
    db.flush()

    return profile


def run_mock_monitor(db):
    return monitor_jobs(
        db,
        sources=[MockJobSource()],
    )


def test_first_monitoring_run_creates_jobs_matches_and_notifications(db):
    profile = make_profile(db, user_id=1)

    result = run_mock_monitor(db)

    assert result["new_jobs"] == 12
    assert result["matches_created"] == 12
    assert result["notifications_created"] == 12

    jobs = db.query(Job).all()
    matches = db.query(JobMatch).all()
    notifications = db.query(Notification).all()

    assert len(jobs) == 12
    assert len(matches) == 12
    assert len(notifications) == 12

    assert all(match.user_id == profile.user_id for match in matches)


def test_second_monitoring_run_does_not_create_duplicate_matches_or_notifications(
    db,
):
    make_profile(db, user_id=1)

    first_result = run_mock_monitor(db)

    assert first_result["new_jobs"] == 12
    assert first_result["matches_created"] == 12
    assert first_result["notifications_created"] == 12

    second_result = run_mock_monitor(db)

    assert second_result["new_jobs"] == 0
    assert second_result["updated_jobs"] == 12
    assert second_result["matches_created"] == 0
    assert second_result["notifications_created"] == 0

    assert db.query(Job).count() == 12
    assert db.query(JobMatch).count() == 12
    assert db.query(Notification).count() == 12


def test_monitoring_handles_multiple_career_profiles(db):
    make_profile(db, user_id=1)
    make_profile(db, user_id=2)

    result = run_mock_monitor(db)

    assert result["new_jobs"] == 12
    assert result["matches_created"] == 24
    assert result["notifications_created"] == 24

    assert db.query(Job).count() == 12
    assert db.query(JobMatch).count() == 24
    assert db.query(Notification).count() == 24

    user_one_matches = (
        db.query(JobMatch)
        .filter(JobMatch.user_id == 1)
        .count()
    )

    user_two_matches = (
        db.query(JobMatch)
        .filter(JobMatch.user_id == 2)
        .count()
    )

    assert user_one_matches == 12
    assert user_two_matches == 12


def test_existing_job_updates_do_not_create_new_notifications(db):
    make_profile(db, user_id=1)

    first_result = run_mock_monitor(db)

    assert first_result["new_jobs"] == 12
    assert first_result["notifications_created"] == 12

    job = (
        db.query(Job)
        .filter(Job.company == "TechFlow")
        .first()
    )

    assert job is not None

    original_job_id = job.id
    original_fingerprint = job.fingerprint

    job.description = "Updated description for an existing job."
    db.commit()

    second_result = run_mock_monitor(db)

    assert second_result["new_jobs"] == 0
    assert second_result["updated_jobs"] == 12
    assert second_result["matches_created"] == 0
    assert second_result["notifications_created"] == 0

    updated_job = db.query(Job).filter(Job.id == original_job_id).first()

    assert updated_job is not None
    assert updated_job.fingerprint == original_fingerprint

    assert db.query(Notification).count() == 12


def test_notifications_use_score_threshold(db):
    make_profile(db, user_id=1)

    run_mock_monitor(db)

    immediate_notifications = (
        db.query(Notification)
        .filter(Notification.notification_type == "immediate")
        .all()
    )

    digest_notifications = (
        db.query(Notification)
        .filter(Notification.notification_type == "digest")
        .all()
    )

    assert immediate_notifications
    assert digest_notifications

    immediate_match_ids = {
        notification.job_match_id
        for notification in immediate_notifications
    }

    digest_match_ids = {
        notification.job_match_id
        for notification in digest_notifications
    }

    for match_id in immediate_match_ids:
        match = db.query(JobMatch).filter(JobMatch.id == match_id).first()

        assert match is not None
        assert match.score > 90

    for match_id in digest_match_ids:
        match = db.query(JobMatch).filter(JobMatch.id == match_id).first()

        assert match is not None
        assert match.score <= 90