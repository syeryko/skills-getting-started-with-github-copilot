import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities data to its original state.

    The application stores activity information in a global `activities`
    dictionary.  Several tests will mutate that dictionary (adding or
    removing participants), so we take a deep copy of the original
    structure before each test and restore it afterwards.
    """
    original = copy.deepcopy(app_module.activities)
    yield
    # clear then update so callers holding references to `activities`
    # see the reset value as well.
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original))


def test_get_activities_returns_initial_data():
    # Arrange
    expected = copy.deepcopy(app_module.activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_post_signup_success():
    # Arrange
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    assert email not in app_module.activities[activity]["participants"]

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity}"
    }
    assert email in app_module.activities[activity]["participants"]


def test_post_signup_duplicate_error():
    # Arrange
    activity = "Chess Club"
    email = app_module.activities[activity]["participants"][0]
    assert email in app_module.activities[activity]["participants"]

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    # ensure nothing was added
    assert app_module.activities[activity]["participants"].count(email) == 1


def test_delete_remove_participant_success():
    # Arrange
    activity = "Chess Club"
    email = app_module.activities[activity]["participants"][0]
    assert email in app_module.activities[activity]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {email} from {activity}"
    }
    assert email not in app_module.activities[activity]["participants"]


def test_delete_remove_nonexistent_error():
    # Arrange
    activity = "Chess Club"
    email = "ghost@mergington.edu"
    assert email not in app_module.activities[activity]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in activity"
