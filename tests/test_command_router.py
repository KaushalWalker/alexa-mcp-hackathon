
import pytest

from app.commands.router import detect_intent


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Add a task to revise Python", "create_task"),
        ("Remind me to read tomorrow", "create_task"),
        ("Show my pending tasks", "list_tasks"),
        ("I finished my interview preparation", "complete_task"),
        ("Change my focus sessions to 30 minutes", "update_preferences"),
        ("Plan my next 45 minutes", "generate_plan"),
        ("Hello DayPilot", "general_chat"),
    ],
)
def test_detect_intent(message, expected):
    assert detect_intent(message) == expected
