
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


def test_find_task_to_complete_matches_explicit_title(monkeypatch):
    from app import voice_api

    monkeypatch.setattr(
        voice_api,
        "load_data",
        lambda: {
            "tasks": [
                {
                    "id": "task-001",
                    "title": "Prepare for AI Engineer interview",
                    "status": "pending",
                }
            ]
        },
    )

    task = voice_api.find_task_to_complete(
        "I finished Prepare for AI Engineer interview."
    )

    assert task["id"] == "task-001"


def test_find_task_to_complete_ignores_vague_request(monkeypatch):
    from app import voice_api

    monkeypatch.setattr(
        voice_api,
        "load_data",
        lambda: {
            "tasks": [
                {
                    "id": "task-001",
                    "title": "Prepare for AI Engineer interview",
                    "status": "pending",
                }
            ]
        },
    )

    task = voice_api.find_task_to_complete("I finished my work.")

    assert task is None


def test_completion_endpoint_marks_task_and_replans(monkeypatch):
    from app import voice_api

    captured = {}

    def fake_complete_task(task_id):
        captured["task_id"] = task_id

    def fake_handle_request(message, plan_date, available_minutes=None):
        captured["available_minutes"] = available_minutes

        return {
            "message": message,
            "plan": {"scheduled": [], "unscheduled": []},
            "plan_summary": "Updated plan for remaining tasks.",
            "assistant_response": "Updated plan.",
            "provider": "mock",
        }

    monkeypatch.setattr(
        voice_api,
        "find_task_to_complete",
        lambda message: {
            "id": "task-001",
            "title": "Prepare for AI Engineer interview",
            "status": "pending",
        },
    )
    monkeypatch.setattr(voice_api, "complete_task", fake_complete_task)
    monkeypatch.setattr(voice_api, "handle_request", fake_handle_request)

    response = client.post(
        "/assistant",
        json={
            "message": (
                "I finished Prepare for AI Engineer interview. "
                "Replan my next 30 minutes."
            ),
            "plan_date": "2026-10-15",
        },
    )

    assert response.status_code == 200
    assert captured["task_id"] == "task-001"
    assert captured["available_minutes"] == 30
    assert response.json()["completed_task"] == (
        "Prepare for AI Engineer interview"
    )
    assert "updated plan" in response.json()["assistant_response"].lower()
