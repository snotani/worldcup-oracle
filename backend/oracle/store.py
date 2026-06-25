"""Persistence for predictions, actual results, and run traces.

What: A small SQLite-backed store that records every prediction the agent makes, the run
trace that produced it, and (later) the real match result.
Why: Evals and the dashboard need a durable, queryable history. SQLite keeps the project
dependency-free and the file easy to inspect on camera.
How it fits: `agent.py` writes here after each prediction; `eval/` reads completed matches;
the FastAPI layer serves rows to the Next.js dashboard.
On camera: "Every call the agent makes is logged here, so we can score it later and replay
exactly what it did."
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import PREDICTIONS_DB
from .schema import StoredPrediction

_SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    model_id TEXT NOT NULL,
    persona TEXT,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    kickoff_utc TEXT,
    predicted_outcome TEXT NOT NULL,
    prob_home REAL NOT NULL,
    prob_draw REAL NOT NULL,
    prob_away REAL NOT NULL,
    predicted_score TEXT,
    confidence REAL NOT NULL,
    rationale TEXT,
    persona_message TEXT,
    actual_outcome TEXT,
    actual_score TEXT,
    trace_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE(match_id, model_id, persona)
);

CREATE TABLE IF NOT EXISTS traces (
    trace_id TEXT PRIMARY KEY,
    match_id INTEGER,
    model_id TEXT,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""


class Store:
    """Thin wrapper around a SQLite database file."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or PREDICTIONS_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def save_prediction(self, sp: StoredPrediction) -> None:
        """Insert or replace a prediction (keyed by match + model + persona)."""
        p = sp.prediction
        self._conn.execute(
            """
            INSERT INTO predictions (
                match_id, model_id, persona, home_team, away_team, kickoff_utc,
                predicted_outcome, prob_home, prob_draw, prob_away, predicted_score,
                confidence, rationale, persona_message, actual_outcome, actual_score,
                trace_id, created_at, payload
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(match_id, model_id, persona) DO UPDATE SET
                predicted_outcome=excluded.predicted_outcome,
                prob_home=excluded.prob_home,
                prob_draw=excluded.prob_draw,
                prob_away=excluded.prob_away,
                predicted_score=excluded.predicted_score,
                confidence=excluded.confidence,
                rationale=excluded.rationale,
                persona_message=excluded.persona_message,
                trace_id=excluded.trace_id,
                created_at=excluded.created_at,
                payload=excluded.payload
            """,
            (
                sp.match_id,
                sp.model_id,
                sp.persona,
                sp.home_team,
                sp.away_team,
                sp.kickoff_utc.isoformat() if sp.kickoff_utc else None,
                p.predicted_outcome,
                p.probabilities.home,
                p.probabilities.draw,
                p.probabilities.away,
                p.predicted_score,
                p.confidence,
                p.rationale,
                sp.persona_message,
                sp.actual_outcome,
                sp.actual_score,
                sp.trace_id,
                sp.created_at.isoformat(),
                sp.model_dump_json(),
            ),
        )
        self._conn.commit()

    def save_trace(self, trace_dict: dict[str, Any], match_id: int | None = None) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO traces (trace_id, match_id, model_id, created_at, payload) "
            "VALUES (?,?,?,?,?)",
            (
                trace_dict["trace_id"],
                match_id,
                trace_dict.get("model_id"),
                datetime.now(UTC).isoformat(),
                json.dumps(trace_dict),
            ),
        )
        self._conn.commit()

    def set_result(self, match_id: int, actual_outcome: str, actual_score: str | None) -> int:
        """Record the real result for a match across all stored predictions."""
        cur = self._conn.execute(
            "UPDATE predictions SET actual_outcome=?, actual_score=? WHERE match_id=?",
            (actual_outcome, actual_score, match_id),
        )
        self._conn.commit()
        return cur.rowcount

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload FROM traces WHERE trace_id=?", (trace_id,)
        ).fetchone()
        return json.loads(row["payload"]) if row else None

    def predictions(
        self, model_id: str | None = None, persona: str | None = None, only_completed: bool = False
    ) -> list[StoredPrediction]:
        """Return stored predictions, optionally filtered."""
        clauses: list[str] = []
        params: list[Any] = []
        if model_id is not None:
            clauses.append("model_id=?")
            params.append(model_id)
        if persona is not None:
            clauses.append("persona IS ?" if persona == "" else "persona=?")
            params.append(None if persona == "" else persona)
        if only_completed:
            clauses.append("actual_outcome IS NOT NULL")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._conn.execute(
            f"SELECT payload, actual_outcome, actual_score FROM predictions{where} "
            "ORDER BY kickoff_utc",
            params,
        ).fetchall()
        out: list[StoredPrediction] = []
        for row in rows:
            sp = StoredPrediction.model_validate_json(row["payload"])
            # The payload is captured at write time; overlay the latest result columns.
            sp.actual_outcome = row["actual_outcome"]
            sp.actual_score = row["actual_score"]
            out.append(sp)
        return out

    def distinct_models(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT model_id FROM predictions ORDER BY model_id"
        ).fetchall()
        return [r["model_id"] for r in rows]
