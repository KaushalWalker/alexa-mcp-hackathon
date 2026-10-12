import os
from app.llm.client import get_llm_client
from app.planner.engine import build_daily_plan
from app.tools.storage import load_data


def handle_request(message: str, plan_date: str) -> dict:
    """Handle a user request and generate a daily plan."""
    message = message.strip()

    if not message:
        raise ValueError("Message cannot be empty.")

    data = load_data()
    plan = build_daily_plan(
        tasks=data["tasks"],
        calendar=data["calendar"],
        preferences=data["preferences"],
        plan_date=plan_date,
    )

    client = get_llm_client()
    response = client.generate(
        f"User request: {message}\n"
        f"Daily plan data: {plan}"
    )

    return {
        "message": message,
        "plan": plan,
        "assistant_response": response,
        "provider": os.getenv("LLM_PROVIDER","mock").strip().lower(),
    }
