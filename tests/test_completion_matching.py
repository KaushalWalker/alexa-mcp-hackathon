
from app import voice_api


def test_completion_matches_exact_title(monkeypatch):
    monkeypatch.setattr(
        voice_api,
        "load_data",
        lambda: {
            "tasks": [
                {
                    "id": "task-001",
                    "title": "prepare my project demo",
                    "status": "pending",
                }
            ]
        },
    )

    result = voice_api.find_task_to_complete(
        "I finished prepare my project demo"
    )

    assert result is not None
    assert result["id"] == "task-001"


def test_completion_matches_natural_language(monkeypatch):
    monkeypatch.setattr(
        voice_api,
        "load_data",
        lambda: {
            "tasks": [
                {
                    "id": "task-001",
                    "title": "prepare my project demo",
                    "status": "pending",
                }
            ]
        },
    )

    result = voice_api.find_task_to_complete(
        "I finished preparing my project demo"
    )

    assert result is not None
    assert result["id"] == "task-001"


def test_completion_without_task_name(monkeypatch):
    monkeypatch.setattr(
        voice_api,
        "load_data",
        lambda: {
            "tasks": [
                {
                    "id": "task-001",
                    "title": "prepare my project demo",
                    "status": "pending",
                }
            ]
        },
    )

    result = voice_api.find_task_to_complete(
        "Mark my task as complete"
    )

    assert result is None


def test_completed_tasks_are_not_matched(monkeypatch):
    monkeypatch.setattr(
        voice_api,
        "load_data",
        lambda: {
            "tasks": [
                {
                    "id": "task-001",
                    "title": "prepare my project demo",
                    "status": "completed",
                }
            ]
        },
    )

    result = voice_api.find_task_to_complete(
        "I finished preparing my project demo"
    )

    assert result is None



def test_completion_matches_demo_task_with_extra_words(monkeypatch):
    monkeypatch.setattr(
        voice_api,
        "load_data",
        lambda: {
            "tasks": [
                {
                    "id": "demo-task-001",
                    "title": "Prepare AI project presentation",
                    "status": "pending",
                }
            ]
        },
    )

    result = voice_api.find_task_to_complete(
        "I finished preparing my AI project presentation"
    )

    assert result is not None
    assert result["id"] == "demo-task-001"