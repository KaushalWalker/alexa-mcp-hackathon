
from datetime import date
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.llm.assistant import handle_request

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
