
from datetime import datetime

from app.planner.engine import build_daily_plan


PREFERENCES = {
    "working_hours_start": "09:00",
    "working_hours_end": "12:00",
    "preferred_focus_minutes": 45,
    "break_minutes": 10,
}


def make_task(task_id, minutes, priority="medium", due_date=None):
    return {
        "id": task_id,
        "title": task_id,
        "priority": priority,
        "duration_minutes": minutes,
        "due_date": due_date,
        "status": "pending",
    }


def test_no_overlapping_sessions():
    tasks = [
        make_task("task-1", 60),
        make_task("task-2", 90),
    ]

    plan = build_daily_plan(
        tasks=tasks,
        calendar=[],
        preferences=PREFERENCES,
        plan_date="2026-10-12",
    )

    sessions = plan["scheduled"]

    for previous, current in zip(sessions, sessions[1:]):
        previous_end = datetime.fromisoformat(previous["end"])
        current_start = datetime.fromisoformat(current["start"])
        assert previous_end <= current_start


def test_respects_calendar_events():
    tasks = [make_task("task-1", 120)]

    calendar = [{
        "id": "event-1",
        "title": "Meeting",
        "start": "2026-10-12T09:30:00",
        "end": "2026-10-12T10:30:00",
    }]

    plan = build_daily_plan(
        tasks=tasks,
        calendar=calendar,
        preferences=PREFERENCES,
        plan_date="2026-10-12",
    )

    meeting_start = datetime.fromisoformat(calendar[0]["start"])
    meeting_end = datetime.fromisoformat(calendar[0]["end"])

    for session in plan["scheduled"]:
        start = datetime.fromisoformat(session["start"])
        end = datetime.fromisoformat(session["end"])

        assert end <= meeting_start or start >= meeting_end


def test_reports_unscheduled_work():
    tasks = [make_task("task-1", 300)]

    plan = build_daily_plan(
        tasks=tasks,
        calendar=[],
        preferences=PREFERENCES,
        plan_date="2026-10-12",
    )

    assert plan["unscheduled"]
    assert plan["unscheduled"][0]["minutes_remaining"] > 0
    assert plan["summary"]["fully_scheduled_tasks"] == 0


def test_prioritizes_overdue_tasks():
    tasks = [
        make_task("normal", 30, "medium", "2026-10-15"),
        make_task("overdue", 30, "high", "2026-10-10"),
    ]

    plan = build_daily_plan(
        tasks=tasks,
        calendar=[],
        preferences=PREFERENCES,
        plan_date="2026-10-12",
    )

    task_sessions = [
        item for item in plan["scheduled"]
        if item.get("task_id")
    ]

    assert task_sessions[0]["task_id"] == "overdue"
    assert task_sessions[0]["overdue"] is True
