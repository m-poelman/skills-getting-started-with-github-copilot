import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client_with_fresh_activities():
    original_activities = copy.deepcopy(activities)
    client = TestClient(app)

    try:
        yield client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_root_redirects_to_static_index(client_with_fresh_activities):
    # Arrange
    client = client_with_fresh_activities

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client_with_fresh_activities):
    # Arrange
    client = client_with_fresh_activities

    # Act
    response = client.get("/activities")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert isinstance(payload, dict)
    assert "Chess Club" in payload
    assert {"description", "schedule", "max_participants", "participants"}.issubset(
        payload["Chess Club"].keys()
    )
    assert isinstance(payload["Chess Club"]["participants"], list)


def test_signup_success(client_with_fresh_activities):
    # Arrange
    client = client_with_fresh_activities
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_unknown_activity_returns_404(client_with_fresh_activities):
    # Arrange
    client = client_with_fresh_activities
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_returns_400(client_with_fresh_activities):
    # Arrange
    client = client_with_fresh_activities
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_full_activity_returns_400(client_with_fresh_activities):
    # Arrange
    client = client_with_fresh_activities
    activity_name = "Basketball Team"
    max_participants = activities[activity_name]["max_participants"]
    activities[activity_name]["participants"] = [
        f"student{i}@mergington.edu" for i in range(max_participants)
    ]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_success(client_with_fresh_activities):
    # Arrange
    client = client_with_fresh_activities
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_unregister_unknown_activity_returns_404(client_with_fresh_activities):
    # Arrange
    client = client_with_fresh_activities
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up_returns_404(client_with_fresh_activities):
    # Arrange
    client = client_with_fresh_activities
    activity_name = "Chess Club"
    email = "not.signed.up@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
