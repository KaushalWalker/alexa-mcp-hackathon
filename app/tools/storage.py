
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_FILE = DATA_DIR / "daypilot_data.json"
DEMO_DATA_FILE = DATA_DIR / "daypilot_demo.json"


DEFAULT_DATA: dict[str, Any] = {
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
        {
            "id": "task-003",
            "title": "Read Python interview questions",
            "priority": "medium",
            "duration_minutes": 45,
            "due_date": None,
            "status": "pending",
        },
    ],
    "calendar": [
        {
            "id": "event-001",
            "title": "Focused study session",
            "start": "2026-10-09T18:00:00",
            "end": "2026-10-09T19:00:00",
        },
        {
            "id": "event-002",
            "title": "Hackathon build session",
            "start": "2026-10-09T19:30:00",
            "end": "2026-10-09T21:00:00",
        },
    ],
    "preferences": {
        "working_hours_start": "09:00",
        "working_hours_end": "21:00",
        "preferred_focus_minutes": 45,
        "break_minutes": 10,
    },
}


DEMO_DATA: dict[str, Any] = {
    "tasks": [
        {
            "id": "demo-task-001",
            "title": "Prepare AI project presentation",
            "priority": "high",
            "duration_minutes": 45,
            "due_date": None,
            "status": "pending",
        },
        {
            "id": "demo-task-002",
            "title": "Review interview questions",
            "priority": "medium",
            "duration_minutes": 30,
            "due_date": None,
            "status": "pending",
        },
        {
            "id": "demo-task-003",
            "title": "Submit hackathon project",
            "priority": "high",
            "duration_minutes": 60,
            "due_date": None,
            "status": "pending",
        },
        {
            "id": "demo-task-004",
            "title": "Read technical documentation",
            "priority": "low",
            "duration_minutes": 20,
            "due_date": None,
            "status": "pending",
        },
    ],
    "calendar": [],
    "preferences": {
        "working_hours_start": "09:00",
        "working_hours_end": "18:00",
        "preferred_focus_minutes": 45,
        "break_minutes": 10,
    },
}


def get_data_file() -> Path:
    """Return the active storage file based on DAYPILOT_MODE."""
    mode = os.getenv("DAYPILOT_MODE", "development").strip().lower()

    if mode == "demo":
        return DEMO_DATA_FILE

    if mode == "development":
        return DATA_FILE

    raise ValueError(
        "DAYPILOT_MODE must be 'development' or 'demo'."
    )


def load_data() -> dict[str, Any]:
    """Load data from the selected storage file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_file = get_data_file()

    if not data_file.exists():
        initial_data = DEMO_DATA if data_file == DEMO_DATA_FILE else DEFAULT_DATA
        save_data(deepcopy(initial_data))

    with data_file.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data: dict[str, Any]) -> None:
    """Persist data to the selected storage file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with get_data_file().open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def reset_demo_data() -> dict[str, Any]:
    """Reset demo data without modifying development data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_data_to_file(DEMO_DATA_FILE, deepcopy(DEMO_DATA))
    return deepcopy(DEMO_DATA)


def save_data_to_file(
    path: Path,
    data: dict[str, Any],
) -> None:
    """Save data to an explicitly selected file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
