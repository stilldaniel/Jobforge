import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    # Not used as a context manager, so the scheduler in the app's
    # lifespan doesn't start.
    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def user(db):
    test_user = User(
        email="preferences@example.com",
        timezone="Africa/Lagos",
    )

    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    return test_user


def test_preferences_default_to_on(client, user):
    response = client.get(
        f"/users/{user.id}/notification-preferences"
    )

    assert response.status_code == 200
    assert response.json() == {
        "job_alerts_enabled": True,
        "high_match_alerts_enabled": True,
        "digest_notifications_enabled": True,
        "email_notifications_enabled": True,
    }


def test_patch_changes_only_the_preferences_sent(client, db, user):
    response = client.patch(
        f"/users/{user.id}/notification-preferences",
        json={"digest_notifications_enabled": False},
    )

    assert response.status_code == 200
    assert response.json() == {
        "job_alerts_enabled": True,
        "high_match_alerts_enabled": True,
        "digest_notifications_enabled": False,
        "email_notifications_enabled": True,
    }

    db.refresh(user)

    assert user.digest_notifications_enabled is False
    assert user.email_notifications_enabled is True


def test_updating_account_details_keeps_preferences(client, db, user):
    client.patch(
        f"/users/{user.id}/notification-preferences",
        json={"email_notifications_enabled": False},
    )

    response = client.put(
        f"/users/{user.id}",
        json={
            "email": "preferences@example.com",
            "full_name": "New Name",
            "timezone": "Africa/Lagos",
        },
    )

    assert response.status_code == 200

    db.refresh(user)

    assert user.full_name == "New Name"
    assert user.email_notifications_enabled is False


def test_preferences_for_unknown_user_return_404(client):
    assert (
        client.get("/users/999/notification-preferences").status_code
        == 404
    )
    assert (
        client.patch(
            "/users/999/notification-preferences",
            json={"job_alerts_enabled": False},
        ).status_code
        == 404
    )


def test_preferences_reject_non_boolean_values(client, user):
    response = client.patch(
        f"/users/{user.id}/notification-preferences",
        json={"job_alerts_enabled": "sometimes"},
    )

    assert response.status_code == 422
