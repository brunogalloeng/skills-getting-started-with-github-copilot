import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as backend_app


@pytest.fixture(autouse=True)
def reset_activities_state():
    snapshot = copy.deepcopy(backend_app.activities)
    yield
    backend_app.activities.clear()
    backend_app.activities.update(snapshot)


@pytest.fixture
def client():
    return TestClient(backend_app.app)


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Soccer Team" in data
    assert "participants" in data["Soccer Team"]


def test_signup_for_activity_success(client):
    activity_name = "Soccer Team"
    new_email = "new.student@mergington.edu"

    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": new_email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
    assert new_email in backend_app.activities[activity_name]["participants"]


def test_signup_for_activity_duplicate_registration_returns_400(client):
    activity_name = "Soccer Team"
    existing_email = backend_app.activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": existing_email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_unknown_activity_returns_404(client):
    response = client.post(
        f"/activities/{quote('Unknown Activity', safe='')}/signup",
        params={"email": "someone@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_success(client):
    activity_name = "Soccer Team"
    email = backend_app.activities[activity_name]["participants"][0]

    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"
    assert email not in backend_app.activities[activity_name]["participants"]


def test_unregister_from_unknown_activity_returns_404(client):
    response = client.delete(
        f"/activities/{quote('Unknown Activity', safe='')}/participants",
        params={"email": "someone@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_non_registered_student_returns_404(client):
    activity_name = "Soccer Team"

    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": "not.registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not registered for this activity"
