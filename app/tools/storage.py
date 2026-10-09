
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_FILE = DATA_DIR / "daypilot_data.json"

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


def load_data() -> dict[str, Any]:
    """Load DayPilot data, creating demo data on first run."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        save_data(DEFAULT_DATA)

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data: dict[str, Any]) -> None:
    """Persist DayPilot data to a local JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
