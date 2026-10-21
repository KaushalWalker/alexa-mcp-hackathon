
import os

from app.llm.client import get_llm_client
from app.planner.engine import build_daily_plan
from app.tools.storage import load_data
from datetime import date, datetime


def get_no_schedule_explanation(plan: dict) -> str | None:
    """Explain why no tasks were scheduled after working hours."""

    stats = plan.get("summary", {})

    if stats.get("pending_tasks", 0) == 0:
        return None

    if plan.get("scheduled"):
        return None

    plan_day = date.fromisoformat(plan["plan_date"])
    today = date.today()

    # Don't apply today's working-hours explanation
    # to a different planning date.
    if plan_day != today:
        return None

    working_end = datetime.fromisoformat(
        plan["working_hours"]["end"]
    )

    if datetime.now() < working_end:
        return None

    pending_count = stats["pending_tasks"]

    return (
        f"Your working hours ended at "
        f"{working_end.strftime('%I:%M %p').lstrip('0')}. "
        f"You still have {pending_count} pending "
        f"{'task' if pending_count == 1 else 'tasks'}. "
        "Would you like to plan them for tomorrow?"
    )


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
        explanation = get_no_schedule_explanation(plan)

        if explanation:
            lines.append(explanation)
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

    provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    plan_summary = build_plan_summary(plan)

    if provider == "mock":
        response = plan_summary
    else:
        try:
            client = get_llm_client()

            prompt = f"""
You are DayPilot, a concise and helpful daily planning assistant.

USER REQUEST:
{message}

DAILY PLAN SUMMARY:
{plan_summary}

SCHEDULE DATA:
{plan}

INSTRUCTIONS:
- Answer the user's request using the supplied plan data.
- Use plain text, not Markdown.
- Do not use asterisks, Markdown headings, or escaped formatting characters.
- Present scheduled tasks with their times and priorities when relevant.
- Keep your answer concise and easy to understand when spoken aloud.
- Do not repeat the entire schedule if the user asked a simple question.
- Do not invent tasks, times, priorities, or completion statuses.
- If the plan summary already answers the request, use it as the basis of your response.
- Do not claim an action was completed unless the data confirms it.
"""

            response = client.generate(prompt)

            if not isinstance(response, str) or not response.strip():
                response = plan_summary
                provider = "fallback"

        except Exception:
            response = plan_summary
            provider = "fallback"

    return {
        "message": message,
        "plan": plan,
        "plan_summary": plan_summary,
        "assistant_response": response,
        "provider": provider,
    }
