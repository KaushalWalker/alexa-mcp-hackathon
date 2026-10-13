
from app.llm.assistant import handle_request, build_plan_summary


def test_assistant_returns_plan_and_response():
    result = handle_request(
        message="Help me organize my day",
        plan_date="2026-10-12",
    )

    assert result["message"] == "Help me organize my day"
    assert result["plan"]["plan_date"] == "2026-10-12"
    assert result["assistant_response"]
    assert result["provider"] == "mock"
    assert result["plan_summary"]


def test_assistant_rejects_empty_message():
    try:
        handle_request(message="   ", plan_date="2026-10-12")
    except ValueError as exc:
        assert str(exc) == "Message cannot be empty."
    else:
        raise AssertionError("Expected ValueError for an empty message")


def test_plan_summary_explains_priorities_and_unscheduled_work():
    plan = {
        "plan_date": "2026-10-12",
        "scheduled": [
            {
                "task_id": "task-001",
                "title": "Finish hackathon project",
                "start": "2026-10-12T09:00",
                "end": "2026-10-12T09:45",
                "duration_minutes": 45,
                "priority": "high",
                "due_date": "2026-10-11",
                "overdue": True,
            }
        ],
        "unscheduled": [
            {
                "task_id": "task-002",
                "title": "Read Python questions",
                "minutes_remaining": 30,
                "reason": "Not enough available time today.",
            }
        ],
        "summary": {
            "pending_tasks": 2,
            "fully_scheduled_tasks": 1,
            "unscheduled_tasks": 1,
            "task_minutes_scheduled": 45,
        },
    }

    summary = build_plan_summary(plan)

    assert "2026-10-12" in summary
    assert "45 minutes" in summary
    assert "Finish hackathon project" in summary
    assert "09:00" in summary
    assert "Read Python questions" in summary
    assert "30 minutes remaining" in summary




def test_handle_request_passes_available_minutes(monkeypatch):
    from app.llm import assistant

    captured = {}

    def fake_load_data():
        return {
            "tasks": [
                {
                    "id": "task-001",
                    "title": "Prepare for interview",
                    "priority": "high",
                    "duration_minutes": 120,
                    "due_date": None,
                    "status": "pending",
                }
            ],
            "calendar": [],
            "preferences": {
                "working_hours_start": "09:00",
                "working_hours_end": "17:00",
                "preferred_focus_minutes": 45,
                "break_minutes": 10,
            },
        }

    class FakeLLM:
        def generate(self, prompt):
            return "Here is your updated plan."

    monkeypatch.setattr(assistant, "load_data", fake_load_data)
    monkeypatch.setattr(
        assistant, "get_llm_client", lambda: FakeLLM()
    )

    result = assistant.handle_request(
        message="I only have 30 minutes",
        plan_date="2099-01-15",
        available_minutes=30,
    )

    assert result["plan"]["summary"]["task_minutes_scheduled"] == 30
    assert result["plan"]["unscheduled"][0]["minutes_remaining"] == 90
    assert result["assistant_response"] == "Here is your updated plan."
