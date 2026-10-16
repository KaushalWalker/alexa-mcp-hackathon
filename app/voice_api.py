
import os
import re
from datetime import date
from pathlib import Path
from app.llm.assistant import handle_request
from app.tools.storage import load_data
from app.server.mcp_server import complete_task, create_task, update_user_preferences
from app.commands.router import detect_intent

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field



from app.llm.assistant import handle_request


load_dotenv()

app = FastAPI(title="DayPilot Voice API")

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    plan_date: date = Field(default_factory=date.today)
    available_minutes: int | None = Field(default=None, ge=1)


def extract_available_minutes(message: str) -> int | None:
    """
    Extract an explicit time budget from common user requests.

    Examples:
    - I only have 30 minutes
    - I have 1 hour
    - Plan my next 90 minutes
    - I have 2 hours and 30 minutes

    Does not interpret unrelated time mentions as a budget.
    """

    text = message.lower().strip()

    hour_unit = r"(?:hours?|hrs?|hr)"
    minute_unit = r"(?:minutes?|mins?|min)"

    hour_match = re.search(
        rf"\b(\d+)\s*{hour_unit}\b",
        text,
    )
    minute_match = re.search(
        rf"\b(\d+)\s*{minute_unit}\b",
        text,
    )

    if not hour_match and not minute_match:
        return None

    # Require wording that indicates available planning time.
    budget_context = re.search(
        r"\b("
        r"(?:i|we)\s+(?:only\s+)?(?:have|got)"
        r"|(?:i|we)\s+(?:have|got)\s+only"
        r"|(?:plan|replan|schedule|organize)\s+(?:my\s+)?next"
        r"|(?:i|we)\s+can\s+(?:spend|work|study)"
        r")\b",
        text,
    )

    if not budget_context:
        return None

    # Avoid treating a number before the context as a budget.
    first_match = min(
        (
            match
            for match in (hour_match, minute_match)
            if match is not None
        ),
        key=lambda match: match.start(),
    )

    if first_match.start() < budget_context.start():
        return None

    hours = int(hour_match.group(1)) if hour_match else 0
    minutes = int(minute_match.group(1)) if minute_match else 0

    total = hours * 60 + minutes

    return total if total > 0 else None

def find_task_to_complete(message: str) -> dict | None:
    """Find one task explicitly identified in a completion request."""

    text = message.lower().strip()

    completion_phrases = (
        "i finished",
        "i have finished",
        "i completed",
        "i have completed",
        "mark as completed",
        "mark it complete",
        "mark it as complete",
    )

    if not any(phrase in text for phrase in completion_phrases):
        return None

    data = load_data()
    matches = []

    for task in data["tasks"]:
        if task.get("status") != "pending":
            continue

        title = task["title"].lower()

        if title in text:
            matches.append(task)

    if len(matches) != 1:
        return None

    return matches[0]

def get_pending_tasks_response() -> dict:
    """Return pending tasks without calling an LLM."""

    data = load_data()

    pending_tasks = [
        task
        for task in data["tasks"]
        if task.get("status") == "pending"
    ]

    if not pending_tasks:
        message = "You're all caught up! No pending tasks."
    else:
        lines = ["Here are your pending tasks:"]

        for index, task in enumerate(pending_tasks, start=1):
            lines.append(f"{index}. {task['title']}")

        message = "\n".join(lines)

    return {
        "assistant_response": message,
        "pending_tasks": pending_tasks,
        "intent": "list_tasks",
        "provider": "rule_based",
    }


def extract_new_task(message: str) -> dict | None:
    """Extract a task title and optional duration from a simple command."""

    text = message.strip()

    patterns = [
        r"^add a task to\s+(.+)$",
        r"^create a task to\s+(.+)$",
        r"^remind me to\s+(.+)$",
        r"^add a task called\s+(.+)$",
        r"^create a task called\s+(.+)$",
    ]

    title = None

    for pattern in patterns:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            break

    if not title:
        return None

    duration = 30
    duration_match = re.search(
        r"\s+for\s+(\d+)\s*(minutes?|mins?)$",
        title,
        re.IGNORECASE,
    )

    if duration_match:
        duration = int(duration_match.group(1))
        title = title[:duration_match.start()].strip()

    if not title:
        return None

    return {
        "title": title,
        "duration_minutes": duration,
        "priority": "medium",
    }


def extract_preference_updates(message: str) -> dict | None:
    """Extract simple preference changes from natural-language commands."""
    text = message.lower()
    updates = {}

    focus_match = re.search(
        r"\b(?:focus time|focus duration|focus)\s+(?:to|of)\s+(\d+)\s*(?:minutes?|mins?)\b",
        text,
    )
    if focus_match:
        updates["preferred_focus_minutes"] = int(focus_match.group(1))

    break_match = re.search(
        r"\bbreak(?: time| duration)?\s+(?:to|of)\s+(\d+)\s*(?:minutes?|mins?)\b",
        text,
    )
    if break_match:
        updates["break_minutes"] = int(break_match.group(1))

    hours_match = re.search(
        r"\bworking hours?\s+(?:from\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?"
        r"\s+to\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b",
        text,
    )
    if hours_match:
        def to_24_hour(hour, minute, meridiem):
            hour = int(hour)
            minute = int(minute or 0)

            if minute > 59 or hour < 1 or hour > 12:
                raise ValueError("Use valid working hours, such as 9 AM to 8 PM.")

            if meridiem == "am":
                hour = hour % 12
            elif meridiem == "pm":
                hour = (hour % 12) + 12

            return f"{hour:02d}:{minute:02d}"

        updates["working_hours_start"] = to_24_hour(
            hours_match.group(1), hours_match.group(2), hours_match.group(3)
        )
        updates["working_hours_end"] = to_24_hour(
            hours_match.group(4), hours_match.group(5), hours_match.group(6)
        )

    return updates or None



@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "DayPilot Voice API",
    }


@app.post("/assistant")
def assistant_endpoint(request: AssistantRequest):
    try:
        intent = detect_intent(request.message)

        if intent == "list_tasks":
            return get_pending_tasks_response()

        if intent == "create_task":
            task_details = extract_new_task(request.message)

            if task_details is None:
                return {
                    "intent": "create_task",
                    "assistant_response":(
                        "Try: 'Add a task to prepare for an interview for 30 minutes.'"

                    ),
                    "provider": "rule_based",
                }

            created_task = create_task(**task_details)

            return{
                "intent": "create_task",
                "created_task": created_task,
                "assistant_response": (
                    f"Done! I've added '{created_task['title']}'"
                    f"to your task list."
                ),
                "provider": "rule_based"
            }


        if intent == "update_preferences":
            updates = extract_preference_updates(request.message)

            if updates is None:
                return {
                    "intent": "update_preferences",
                    "assistant_response": (
                        "Try: 'Set my focus time to 25 minutes', "
                        "'Change my break time to 5 minutes', or "
                        "'Set my working hours from 9 AM to 8 PM'."
                    ),
                    "provider": "rule_based",
                }

            preferences = update_user_preferences(**updates)

            return {
                "intent": "update_preferences",
                "preferences": preferences,
                "assistant_response": (
                    "Done! I've updated your planning preferences."
                ),
                "provider": "rule_based",
            }



        completed_task = find_task_to_complete(request.message)

        if completed_task is not None:
            complete_task(completed_task["id"])

            # Rebuild the plan after the task is marked complete.
            result = handle_request(
                message=request.message,
                plan_date=request.plan_date.isoformat(),
                available_minutes=(
                    request.available_minutes
                    if request.available_minutes is not None
                    else extract_available_minutes(request.message)
                ),
            )

            result["available_minutes"] = (
                request.available_minutes
                if request.available_minutes is not None
                else extract_available_minutes(request.message)
            )
            result["completed_task"] = completed_task["title"]
            result["assistant_response"] = (
                f"Great work! I've marked '{completed_task['title']}' "
                f"as completed. Here's your updated plan.\n\n"
                f"{result['plan_summary']}"
            )

            return result

        # Explicit API value takes priority over message extraction.
        available_minutes = request.available_minutes

        if available_minutes is None:
            available_minutes = extract_available_minutes(
                request.message
            )

        result = handle_request(
            message=request.message,
            plan_date=request.plan_date.isoformat(),
            available_minutes=available_minutes,
        )

        result["available_minutes"] = available_minutes

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="DayPilot couldn't process this request.",
        ) from exc




@app.post("/speech")
def generate_speech(request: AssistantRequest):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI speech is not configured.",
        )

    text = request.message.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty.",
        )

    try:
        client = OpenAI(api_key=api_key)

        audio = client.audio.speech.create(
            model=os.getenv(
                "OPENAI_TTS_MODEL",
                "gpt-4o-mini-tts",
            ),
            voice=os.getenv(
                "OPENAI_TTS_VOICE",
                "marin",
            ),
            input=text[:4000],
            instructions=(
                "Speak naturally and clearly in Indian English, "
                "with a warm, calm, encouraging tone and "
                "conversational pacing."
            ),
            response_format="mp3",
        )

        return Response(
            content=audio.content,
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-store"},
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Natural speech is temporarily unavailable.",
        ) from exc
