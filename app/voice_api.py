import os 
from datetime import date
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from io import BytesIO 
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from openai import OpenAI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.llm.assistant import handle_request

load_dotenv()

app = FastAPI(title="DayPilot Voice API")

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
)


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    plan_date: date = Field(default_factory=date.today)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "DayPilot Voice API"}


@app.post("/assistant")
def assistant_endpoint(request: AssistantRequest):
    try:
        result = handle_request(
            message=request.message,
            plan_date=request.plan_date.isoformat(),
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        client = OpenAI(api_key=api_key)

        audio = client.audio.speech.create(
            model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
            voice=os.getenv("OPENAI_TTS_VOICE", "marin"),
            input=text[:4000],
            instructions=(
                "Speak naturally and clearly in Indian English, "
                "with a warm, calm, encouraging tone and conversational pacing."
            ),
            response_format="mp3",
        )

        return Response(
            content=audio.content,
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-store"},
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Natural speech is temporarily unavailable.",
        )

