
from datetime import date, timedelta

from app.voice_api import extract_plan_date
from app.voice_api import extract_new_task


def test_extract_task_with_duration():
    result = extract_new_task(
        "Add a task to practice my presentation for 15 minutes"
    )

    assert result is not None
    assert result["title"] == "practice my presentation"
    assert result["duration_minutes"] == 15


def test_extract_task_with_duration_and_period():
    result = extract_new_task(
        "Add a task to practice my presentation for 15 minutes."
    )

    assert result is not None
    assert result["title"] == "practice my presentation"
    assert result["duration_minutes"] == 15


def test_extract_task_uses_default_duration():
    result = extract_new_task(
        "Add a task to practice my presentation."
    )

    assert result is not None
    assert result["title"] == "practice my presentation"
    assert result["duration_minutes"] == 30



def test_extract_plan_date_tomorrow():
    today = date(2026, 10, 21)

    result = extract_plan_date(
        "Plan my remaining tasks for tomorrow",
        today,
    )

    assert result == today + timedelta(days=1)


def test_extract_plan_date_day_after_tomorrow():
    today = date(2026, 10, 21)

    result = extract_plan_date(
        "Plan my tasks for the day after tomorrow",
        today,
    )

    assert result == today + timedelta(days=2)


def test_extract_plan_date_without_date_keeps_default():
    today = date(2026, 10, 21)

    result = extract_plan_date("Plan my tasks", today)

    assert result == today