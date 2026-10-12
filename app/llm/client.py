
from typing import Protocol
import os 

class LLMClient(Protocol):
    """Common interface for DayPilot language model clients."""

    def generate(self, prompt: str) -> str:
        """Generate a response from a prompt."""
        ...


class MockLLMClient:
    """Local mock client for development without API costs."""

    def generate(self, prompt: str) -> str:
        prompt = prompt.strip()

        if not prompt:
            return "Please tell me what you need help with."

        return (
            "DayPilot AI (mock mode): I received your request: "
            f"{prompt}\n\n"
            "I can connect this request to DayPilot's planning tools "
            "once the AI integration is configured."
        )


def get_llm_client() -> LLMClient:
    """Select the configured language model provider. """
    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()

    if provider == "mock":
        return MockLLMClient()

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {provider !r}."
        "Only 'mock' is currently available."
    )

