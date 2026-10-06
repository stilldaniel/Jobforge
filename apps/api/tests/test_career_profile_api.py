import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.notification import Notification
from app.models.user import User


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    # Not used as a context manager, so the scheduler doesn't start.
    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def user(db):
    test_user = User(
        email="profile@example.com",
        timezone="Africa/Lagos",
    )

    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    return test_user


def make_job(db, title, skills, fingerprint):
    job = Job(
        title=title,
        company="Test Company",
        required_skills=skills,
        location="Remote",
        remote_eligibility="Worldwide",
        work_type="remote",
        application_url=f"https://example.com/{fingerprint}",
        source="test",
        fingerprint=fingerprint,
    )

    db.add(job)
    db.commit()

    return job


PROFILE = {
    "professional_title": "Backend Developer",
    "skills": '["Python"]',
    "years_of_experience": 3,
    "candidate_location": "Lagos, Nigeria",
    "preferred_work_type": "remote",
}


def test_saving_profile_rescores_existing_matches(client, db, user):
    react_job = make_job(
        db,
        "Frontend Developer",
        '["React", "TypeScript"]',
        "react-job",
    )

    client.post(f"/users/{user.id}/career-profile/", json=PROFILE)

    match = db.query(JobMatch).filter_by(job_id=react_job.id).one()
    backend_score = match.score

    response = client.put(
        f"/users/{user.id}/career-profile/",
        json={
            **PROFILE,
            "professional_title": "Frontend Developer",
            "skills": '["React", "TypeScript"]',
        },
    )

    assert response.status_code == 200

    db.refresh(match)

    assert match.score > backend_score
    assert match.score > 90


def test_saving_profile_matches_jobs_without_a_match(client, db, user):
    make_job(db, "Frontend Developer", '["React"]', "first-job")
    make_job(db, "React Developer", '["React"]', "second-job")

    client.post(f"/users/{user.id}/career-profile/", json=PROFILE)

    assert db.query(JobMatch).filter_by(user_id=user.id).count() == 2


def test_saving_profile_does_not_send_notifications(client, db, user):
    make_job(db, "Backend Developer", '["Python"]', "python-job")

    client.post(f"/users/{user.id}/career-profile/", json=PROFILE)

    assert db.query(Notification).count() == 0


def test_salary_currency_and_period_are_saved(client, user):
    response = client.post(
        f"/users/{user.id}/career-profile/",
        json={
            **PROFILE,
            "minimum_salary": 3000,
            "salary_currency": " usd ",
            "salary_period": "month",
        },
    )

    assert response.status_code == 200
    assert response.json()["salary_currency"] == "USD"
    assert response.json()["salary_period"] == "month"


@pytest.mark.parametrize(
    "field, value",
    [
        ("salary_currency", "US Dollars"),
        ("salary_currency", "U1D"),
        ("salary_period", "week"),
    ],
)
def test_invalid_salary_settings_are_rejected(client, user, field, value):
    response = client.post(
        f"/users/{user.id}/career-profile/",
        json={**PROFILE, field: value},
    )

    assert response.status_code == 422
