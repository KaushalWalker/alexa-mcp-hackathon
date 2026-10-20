
from copy import deepcopy

import pytest

from app.tools import storage


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """Keep Demo Mode tests isolated from real project data."""
    data_dir = tmp_path / "data"

    monkeypatch.setattr(storage, "DATA_DIR", data_dir)
    monkeypatch.setattr(storage, "DATA_FILE", data_dir / "daypilot_data.json")
    monkeypatch.setattr(
        storage, "DEMO_DATA_FILE", data_dir / "daypilot_demo.json"
    )
    monkeypatch.setenv("DAYPILOT_MODE", "development")

    return data_dir


def test_development_and_demo_data_are_separate(isolated_storage, monkeypatch):
    development_data = storage.load_data()

    monkeypatch.setenv("DAYPILOT_MODE", "demo")
    demo_data = storage.load_data()

    assert storage.DATA_FILE.exists()
    assert storage.DEMO_DATA_FILE.exists()
    assert development_data == storage.DEFAULT_DATA
    assert demo_data == storage.DEMO_DATA

    # Changes in Demo Mode must not affect development data.
    demo_data["tasks"].append(
        {
            "id": "test-task",
            "title": "Demo-only task",
            "priority": "low",
            "duration_minutes": 10,
            "due_date": None,
            "status": "pending",
        }
    )
    storage.save_data(demo_data)

    monkeypatch.setenv("DAYPILOT_MODE", "development")
    assert storage.load_data() == development_data


def test_reset_demo_data_restores_demo_defaults(isolated_storage, monkeypatch):
    monkeypatch.setenv("DAYPILOT_MODE", "demo")
    storage.load_data()

    modified_data = storage.load_data()
    modified_data["tasks"] = []
    storage.save_data(modified_data)

    reset_data = storage.reset_demo_data()

    assert reset_data == storage.DEMO_DATA
    assert storage.load_data() == storage.DEMO_DATA


def test_invalid_mode_raises_error(isolated_storage, monkeypatch):
    monkeypatch.setenv("DAYPILOT_MODE", "invalid")

    with pytest.raises(ValueError, match="DAYPILOT_MODE"):
        storage.load_data()
