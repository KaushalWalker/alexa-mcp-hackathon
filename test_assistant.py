
import pytest

from app.llm.assistant import handle_request


def test_assistant_returns_plan_and_response():
    result = handle_request(
        "Help me organize my day",
        "2026-10-12",
    )

    assert result["message"] == "Help me organize my day"
    assert result["plan"]["plan_date"] == "2026-10-12"
    assert result["assistant_response"]
    assert result["provider"] == "mock"


def test_assistant_rejects_empty_message():
    with pytest.raises(ValueError, match="Message cannot be empty"):
        handle_request("   ", "2026-10-12")
