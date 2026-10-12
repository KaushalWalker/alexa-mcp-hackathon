
from app.llm.client import get_llm_client


def test_mock_client_returns_response():
    client = get_llm_client()

    response = client.generate("Help me plan my day")

    assert "Help me plan my day" in response
    assert "mock mode" in response


def test_mock_client_handles_empty_prompt():
    client = get_llm_client()

    response = client.generate("   ")

    assert response == "Please tell me what you need help with."
