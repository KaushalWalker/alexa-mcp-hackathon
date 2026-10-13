
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
