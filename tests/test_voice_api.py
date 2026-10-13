
from fastapi.testclient import TestClient

from app.voice_api import app, extract_available_minutes


client = TestClient(app)


def test_extract_30_minutes():
    assert extract_available_minutes(
        "I only have 30 minutes today"
    ) == 30


def test_extract_one_hour():
    assert extract_available_minutes(
        "I have 1 hour to study"
    ) == 60


def test_extract_hours_and_minutes():
    assert extract_available_minutes(
        "I have 2 hours and 30 minutes"
    ) == 150


def test_unrelated_time_does_not_set_budget():
    assert extract_available_minutes(
        "My meeting starts in 30 minutes"
    ) is None


def test_assistant_endpoint_respects_time_limit(monkeypatch):
    from app import voice_api

    captured = {}

    def fake_handle_request(
        message,
        plan_date,
        available_minutes=None,
    ):
        captured["available_minutes"] = available_minutes
        captured["plan_date"] = plan_date

        return {
            "message": message,
            "plan": {},
            "plan_summary": "Test summary",
            "assistant_response": "Test response",
            "provider": "mock",
        }

    monkeypatch.setattr(
        voice_api,
        "handle_request",
        fake_handle_request,
    )

    response = client.post(
        "/assistant",
        json={
            "message": "I only have 30 minutes today",
            "plan_date": "2026-10-14",
        },
    )

    assert response.status_code == 200
    assert captured["available_minutes"] == 30
    assert captured["plan_date"] == "2026-10-14"
    assert response.json()["available_minutes"] == 30
