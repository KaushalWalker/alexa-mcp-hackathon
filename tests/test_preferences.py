
import json
from copy import deepcopy
from app.planner.engine import build_daily_plan
import pytest

from app.server import mcp_server
from app.tools import storage


@pytest.fixture
def isolated_data(tmp_path, monkeypatch):
    """Keep tests away from the real DayPilot data file."""
    data_dir = tmp_path / "data"
    data_file = data_dir / "daypilot_data.json"

    monkeypatch.setattr(storage, "DATA_DIR", data_dir)
    monkeypatch.setattr(storage, "DATA_FILE", data_file)
    monkeypatch.setattr(mcp_server, "load_data", storage.load_data)
    monkeypatch.setattr(mcp_server, "save_data", storage.save_data)

    storage.save_data(deepcopy(storage.DEFAULT_DATA))


def test_update_preferences_persists_changes(isolated_data):
    result = mcp_server.update_user_preferences(
        preferred_focus_minutes=50,
        break_minutes=5,
    )

    saved = json.loads(storage.DATA_FILE.read_text(encoding="utf-8"))

    assert result["preferred_focus_minutes"] == 50
    assert result["break_minutes"] == 5
    assert result["working_hours_start"] == "09:00"
    assert saved["preferences"] == result


def test_update_preferences_rejects_invalid_working_hours(isolated_data):
    with pytest.raises(ValueError, match="end after"):
        mcp_server.update_user_preferences(
            working_hours_start="21:00",
            working_hours_end="09:00",
        )


def test_update_preferences_rejects_invalid_focus_duration(isolated_data):
    with pytest.raises(ValueError, match="positive integer"):
        mcp_server.update_user_preferences(preferred_focus_minutes=0)


def test_update_preferences_rejects_negative_break(isolated_data):
    with pytest.raises(ValueError, match="non-negative integer"):
        mcp_server.update_user_preferences(break_minutes=-1)


def test_update_preferences_rejects_invalid_time_format(isolated_data):
    with pytest.raises(ValueError, match="HH:MM"):
        mcp_server.update_user_preferences(working_hours_start="9am")


def test_updated_focus_preference_changes_plan(isolated_data):
    mcp_server.update_user_preferences(
        working_hours_start="09:00",
        working_hours_end="12:00",
        preferred_focus_minutes=25,
        break_minutes=0,
    )
    preferences = mcp_server.get_user_preferences()

    tasks = [
        {
            "id": "task-test",
            "title": "Prepare interview",
            "priority": "high",
            "duration_minutes": 60,
            "due_date": None,
            "status": "pending",
        }
    ]

    plan = build_daily_plan(
        tasks=tasks,
        calendar=[],
        preferences=preferences,
        plan_date="2099-01-01",
    )

    work_sessions = [
        item for item in plan["scheduled"]
        if item.get("task_id") == "task-test"
    ]

    assert len(work_sessions) == 3
    assert [item["duration_minutes"] for item in work_sessions] == [
        25, 25, 10
    ]
