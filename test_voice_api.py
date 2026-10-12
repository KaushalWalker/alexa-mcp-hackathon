
from fastapi.testclient import TestClient

from app.voice_api import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_assistant_endpoint_returns_plan():
    response = client.post(
        "/assistant",
        json={
            "message": "Help me organize my day",
            "plan_date": "2026-10-12",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Help me organize my day"
    assert data["plan"]["plan_date"] == "2026-10-12"
    assert data["assistant_response"]
    assert data["provider"] == "mock"


def test_assistant_endpoint_rejects_empty_message():
    response = client.post(
        "/assistant",
        json={
            "message": "",
            "plan_date": "2026-10-12",
        },
    )

    assert response.status_code == 422
