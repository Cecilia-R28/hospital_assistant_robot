from app import app


def test_home_page_returns_200():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_valid_orientation_request():
    client = app.test_client()
    response = client.post(
        "/api/request",
        json={"category": "ORIENTATION", "item": "PHARMACY"},
    )

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert response.get_json()["request"] == {
        "category": "ORIENTATION",
        "destination": "PHARMACY",
    }


def test_information_response_has_title_and_disclaimer():
    client = app.test_client()
    response = client.post(
        "/api/request",
        json={"category": "INFORMATION", "item": "HIV"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "VIH / SIDA"
    assert "non diagnostique" in data["message"]


def test_unknown_item_returns_400():
    client = app.test_client()
    response = client.post(
        "/api/request",
        json={"category": "ORIENTATION", "item": "UNKNOWN_DESTINATION"},
    )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_empty_body_returns_400():
    client = app.test_client()
    response = client.post(
        "/api/request",
        data="",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
