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
    # Arrange

    # Act
    response = client.get("/activities")
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert isinstance(data, dict)
    assert "Soccer Team" in data
    assert "participants" in data["Soccer Team"]


def test_signup_for_activity_success(client):
    # Arrange
    activity_name = "Soccer Team"
    new_email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": new_email},
    )
    result = response.json()

    # Assert
    assert response.status_code == 200
    assert result["message"] == f"Signed up {new_email} for {activity_name}"
    assert new_email in backend_app.activities[activity_name]["participants"]


def test_signup_for_activity_duplicate_registration_returns_400(client):
    # Arrange
    activity_name = "Soccer Team"
    existing_email = backend_app.activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": existing_email},
    )
    result = response.json()

    # Assert
    assert response.status_code == 400
    assert result["detail"] == "Student already signed up for this activity"


def test_signup_for_unknown_activity_returns_404(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "someone@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )
    result = response.json()

    # Assert
    assert response.status_code == 404
    assert result["detail"] == "Activity not found"


def test_unregister_participant_success(client):
    # Arrange
    activity_name = "Soccer Team"
    email = backend_app.activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": email},
    )
    result = response.json()

    # Assert
    assert response.status_code == 200
    assert result["message"] == f"Removed {email} from {activity_name}"
    assert email not in backend_app.activities[activity_name]["participants"]


def test_unregister_from_unknown_activity_returns_404(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "someone@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": email},
    )
    result = response.json()

    # Assert
    assert response.status_code == 404
    assert result["detail"] == "Activity not found"


def test_unregister_non_registered_student_returns_404(client):
    # Arrange
    activity_name = "Soccer Team"
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": email},
    )
    result = response.json()

    # Assert
    assert response.status_code == 404
    assert result["detail"] == "Student not registered for this activity"
