"""FastAPI server: serves live agent data to the dashboard.

What: A small HTTP API exposing fixtures, predictions, the battle leaderboard, the scoreboard,
persona cards, and run traces.
Why: For a live demo you want the dashboard to call the agent on demand rather than a static
export. Same payload builder as the CLI export, so both stay in sync.
How it fits: The Next.js dashboard fetches these endpoints; falls back to static JSON if the
server isn't running.
On camera: "The dashboard is just a thin view over these endpoints the agent serves."

Run: uvicorn oracle.api:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .agent import predict_match
from .config import get_settings
from .dashboard import build_payload
from .eval.backtest import run_backtest
from .store import Store
from .tools import get_provider

app = FastAPI(title="The Oracle API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    s = get_settings()
    return {
        "ok": True,
        "has_cursor_key": s.has_cursor_key,
        "has_football_key": s.has_football_key,
        "mock_data": s.use_mock_data,
    }


@app.get("/api/dashboard")
def dashboard(mock: bool = False, persona: str = "gaffer", limit: int = 8) -> dict:
    """The full dashboard payload (all three angles)."""
    return build_payload(mock_model=mock, persona=persona, upcoming_limit=limit)


@app.get("/api/fixtures")
def fixtures(status: str | None = None) -> list[dict]:
    return get_provider().list_fixtures(status=status)


@app.get("/api/scoreboard")
def scoreboard(model: str | None = None, mock: bool = False) -> dict:
    return run_backtest(model, mock_model=mock).to_dict()


@app.post("/api/predict")
def predict(match_id: int, model: str | None = None, persona: str | None = None,
            mock: bool = False) -> dict:
    stored, trace = predict_match(
        match_id, model_id=model, persona=persona, mock_model=mock, save=False
    )
    return {"prediction": stored.model_dump(mode="json"), "trace": trace.to_dict()}


@app.get("/api/trace/{trace_id}")
def trace(trace_id: str) -> dict:
    with Store() as store:
        data = store.get_trace(trace_id)
    if data is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return data
