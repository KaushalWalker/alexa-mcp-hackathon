
from datetime import date
from uuid import uuid4
from mcp.server.fastmcp import FastMCP

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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
