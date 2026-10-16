
from datetime import date
from uuid import uuid4
from mcp.server.fastmcp import FastMCP
from app.planner.engine import build_daily_plan

from app.tools.storage import load_data, save_data

mcp = FastMCP("DayPilot")


@mcp.tool()
def get_tasks(status: str = "all") -> list[dict]:
    """Get DayPilot tasks. Status can be all, pending, or completed."""
    if status not in {"all", "pending", "completed"}:
        raise ValueError("Status must be all, pending, or completed.")

    tasks = load_data()["tasks"]

    if status == "all":
        return tasks

    return [task for task in tasks if task["status"] == status]


@mcp.tool()
def get_calendar() -> list[dict]:
    """Get the user's calendar events."""
    return load_data()["calendar"]


@mcp.tool()
def get_deadlines() -> list[dict]:
    """Get tasks with due dates, ordered by the nearest deadline."""
    tasks = load_data()["tasks"]

    dated_tasks = [
        task for task in tasks
        if task.get("due_date")
    ]

    return sorted(
        dated_tasks,
        key=lambda task: task["due_date"],
    )


@mcp.tool()
def get_user_preferences() -> dict:
    """Get the user's working hours and focus-session preferences."""
    return load_data()["preferences"]


@mcp.tool()
def update_user_preferences(
    working_hours_start: str | None = None,
    working_hours_end: str | None = None,
    preferred_focus_minutes: int | None = None,
    break_minutes: int | None = None,
) -> dict:
    """Update and save the user's planning preferences.

    Only supplied values are changed. Omitted values stay unchanged.
    Times use HH:MM in 24-hour format.
    """
    from datetime import datetime

    updates = {}

    if working_hours_start is not None:
        updates["working_hours_start"] = working_hours_start

    if working_hours_end is not None:
        updates["working_hours_end"] = working_hours_end

    if preferred_focus_minutes is not None:
        updates["preferred_focus_minutes"] = preferred_focus_minutes

    if break_minutes is not None:
        updates["break_minutes"] = break_minutes

    data = load_data()
    preferences = data["preferences"].copy()
    preferences.update(updates)

    # Validate times and ensure the working day has a valid range.
    try:
        start = datetime.strptime(
            preferences["working_hours_start"], "%H:%M"
        )
        end = datetime.strptime(
            preferences["working_hours_end"], "%H:%M"
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("Working hours must use HH:MM format.") from exc

    if start.strftime("%H:%M") != preferences["working_hours_start"]:
        raise ValueError("Working hours must use HH:MM format.")

    if end.strftime("%H:%M") != preferences["working_hours_end"]:
        raise ValueError("Working hours must use HH:MM format.")

    if end <= start:
        raise ValueError("Working hours must end after they start.")

    focus = preferences["preferred_focus_minutes"]
    breaks = preferences["break_minutes"]

    if isinstance(focus, bool) or not isinstance(focus, int) or focus < 1:
        raise ValueError("Focus duration must be a positive integer.")

    if isinstance(breaks, bool) or not isinstance(breaks, int) or breaks < 0:
        raise ValueError("Break duration must be a non-negative integer.")

    data["preferences"] = preferences
    save_data(data)

    return preferences


@mcp.tool()
def create_task(
    title: str,
    priority: str = "medium",
    duration_minutes: int = 30,
    due_date: str | None = None,
) -> dict:
    """Create and save a task with an optional YYYY-MM-DD deadline."""
    title = title.strip()

    if not title:
        raise ValueError("Task title cannot be empty.")

    if priority not in {"low", "medium", "high"}:
        raise ValueError("Priority must be low, medium, or high.")

    if not 1 <= duration_minutes <= 1440:
        raise ValueError("Duration must be between 1 and 1440 minutes.")

    if due_date is not None:
        parsed_date = date.fromisoformat(due_date)
        if parsed_date.isoformat() != due_date:
            raise ValueError("Use the YYYY-MM-DD date format.")

    data = load_data()

    task = {
        "id": f"task-{uuid4().hex[:8]}",
        "title": title,
        "priority": priority,
        "duration_minutes": duration_minutes,
        "due_date": due_date,
        "status": "pending",
    }

    data["tasks"].append(task)
    save_data(data)

    return task

@mcp.tool()
def generate_daily_plan(plan_date: str) -> dict:
    """
    Generate a daily schedule using saved tasks, calendar
    events, and user preferences.

    plan_date must be in YYYY-MM-DD format.
    """
    date.fromisoformat(plan_date)

    data = load_data()

    return build_daily_plan(
        tasks=data["tasks"],
        calendar=data["calendar"],
        preferences=data["preferences"],
        plan_date=plan_date,
    )


@mcp.tool()
def complete_task(task_id: str) -> dict:
    """Mark an existing task as completed and save the change."""
    data = load_data()

    for task in data["tasks"]:
        if task["id"] == task_id:
            if task["status"] == "completed":
                return task

            task["status"] = "completed"
            save_data(data)
            return task

    raise ValueError(f"Task not found: {task_id}")


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
