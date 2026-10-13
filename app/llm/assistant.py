
import os

from app.llm.client import get_llm_client
from app.planner.engine import build_daily_plan
from app.tools.storage import load_data


def build_plan_summary(plan: dict) -> str:
    scheduled = plan.get("scheduled", [])
    unscheduled = plan.get("unscheduled", [])
    stats = plan.get("summary", {})

    work_blocks = [
        item
        for item in scheduled
        if item.get("task_id") is not None
        and item.get("type") != "break"
    ]

    lines = [
        f"Your plan for {plan['plan_date']} is ready.",
        f"{stats.get('task_minutes_scheduled', 0)} minutes of task work are scheduled.",
        f"{stats.get('fully_scheduled_tasks', 0)} tasks are fully scheduled.",
    ]

    overdue_titles = []

    for item in work_blocks:
        if item.get("overdue") and item["title"] not in overdue_titles:
            overdue_titles.append(item["title"])

    if overdue_titles:
        lines.append(
            "Overdue tasks to prioritize: "
            + ", ".join(overdue_titles)
            + "."
        )

    if work_blocks:
        first_block = min(work_blocks, key=lambda item: item["start"])
        lines.append(
            f"Start with '{first_block['title']}' at "
            f"{first_block['start'][11:16]}."
        )
    else:
        lines.append("No task work could be scheduled for this day.")

    if unscheduled:
        lines.append("Tasks needing more time:")

        for task in unscheduled:
            lines.append(
                f"- {task['title']}: "
                f"{task['minutes_remaining']} minutes remaining."
            )
    else:
        lines.append("All pending tasks fit into the available schedule.")

    return "\n".join(lines)


def handle_request(
    message: str,
    plan_date: str,
    available_minutes: int | None = None,
) -> dict:
    message = message.strip()

    if not message:
        raise ValueError("Message cannot be empty.")

    data = load_data()

    plan = build_daily_plan(
        tasks=data["tasks"],
        calendar=data["calendar"],
        preferences=data["preferences"],
        plan_date=plan_date,
        available_minutes=available_minutes,
    )

    client = get_llm_client()

    response = client.generate(
        f"User request: {message}\n"
        f"Daily plan data: {plan}"
    )

    return {
        "message": message,
        "plan": plan,
        "plan_summary": build_plan_summary(plan),
        "assistant_response": response,
        "provider": os.getenv("LLM_PROVIDER", "mock").strip().lower(),
    }
