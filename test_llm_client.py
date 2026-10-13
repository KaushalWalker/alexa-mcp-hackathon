
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.llm.client import (
    MockLLMClient,
    OpenAILLMClient,
    get_llm_client,
)


def test_mock_client_returns_response(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    client = get_llm_client()
    response = client.generate("Help me plan my day")

    assert "Help me plan my day" in response
    assert "mock mode" in response


def test_mock_client_handles_empty_prompt(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    client = get_llm_client()
    response = client.generate("   ")

    assert response == "Please tell me what you need help with."


def test_mock_provider_is_default(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    client = get_llm_client()

    assert isinstance(client, MockLLMClient)


def test_openai_provider_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is missing"):
        get_llm_client()


def test_openai_provider_generates_response(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="Start with your highest-priority task."
                )
            )
        ]
    )

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response

    fake_openai_class = MagicMock(return_value=fake_client)
    fake_openai_module = SimpleNamespace(OpenAI=fake_openai_class)

    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)

    client = get_llm_client()
    result = client.generate("Help me organize my day.")

    assert isinstance(client, OpenAILLMClient)
    assert result == "Start with your highest-priority task."

    fake_client.chat.completions.create.assert_called_once()

    call_kwargs = fake_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"
    assert call_kwargs["messages"][1]["content"] == (
        "Help me organize my day."
    )


def test_openai_provider_handles_empty_model_response(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")

    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=None)
            )
        ]
    )

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response

    fake_openai_class = MagicMock(return_value=fake_client)
    fake_openai_module = SimpleNamespace(OpenAI=fake_openai_class)

    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)

    client = get_llm_client()

    assert client.generate("Help me plan.") == (
        "I couldn't generate a response. Please try again."
    )
