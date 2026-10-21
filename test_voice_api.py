
from fastapi.testclient import TestClient

from app.voice_api import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_assistant_endpoint_returns_plan(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
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


def test_real_completion_persists_and_replans_in_temporary_data(
    monkeypatch,
    tmp_path,
):
    import json

    from app import voice_api
    from app.server import mcp_server
    from app.tools import storage
    from app.planner.engine import build_daily_plan

    test_file = tmp_path / "daypilot_data.json"

    test_data = {
        "tasks": [
            {
                "id": "task-001",
                "title": "Prepare for AI Engineer interview",
                "priority": "high",
                "duration_minutes": 60,
                "due_date": "2026-10-10",
                "status": "pending",
            },
            {
                "id": "task-002",
                "title": "Finish hackathon project",
                "priority": "high",
                "duration_minutes": 120,
                "due_date": "2026-10-12",
                "status": "pending",
            },
        ],
        "calendar": [],
        "preferences": {
            "working_hours_start": "09:00",
            "working_hours_end": "21:00",
            "preferred_focus_minutes": 45,
            "break_minutes": 10,
        },
    }

    test_file.write_text(json.dumps(test_data), encoding="utf-8")

    monkeypatch.setenv("DAYPILOT_MODE", "development")
    monkeypatch.setattr(storage, "DATA_FILE", test_file)
    monkeypatch.setattr(
        storage,
        "DEMO_DATA_FILE",
        tmp_path / "daypilot_demo.json",
    )
    monkeypatch.setattr(mcp_server, "load_data", storage.load_data)
    monkeypatch.setattr(mcp_server, "save_data", storage.save_data)

    completed = mcp_server.complete_task("task-001")

    saved_data = json.loads(test_file.read_text(encoding="utf-8"))

    assert completed["status"] == "completed"
    assert saved_data["tasks"][0]["status"] == "completed"

    plan = build_daily_plan(
        tasks=saved_data["tasks"],
        calendar=saved_data["calendar"],
        preferences=saved_data["preferences"],
        plan_date="2026-10-15",
        available_minutes=30,
    )

    scheduled_task_ids = {
        item.get("task_id")
        for item in plan["scheduled"]
        if item.get("task_id") is not None
    }

    assert "task-001" not in scheduled_task_ids
    assert plan["summary"]["task_minutes_scheduled"] <= 30
