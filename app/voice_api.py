
import os
import re
from datetime import date
from pathlib import Path

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
        r"|(?:plan|schedule|organize)\s+(?:my\s+)?next"
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


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "DayPilot Voice API",
    }


@app.post("/assistant")
def assistant_endpoint(request: AssistantRequest):
    try:
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
