"""The prediction contract (spec-driven development in code).

What: Pydantic models that define exactly what the agent receives and must return.
Why: The output schema IS the agent's contract. Defining it first (from spec/AGENT_SPEC.md)
means the model is forced into a structured, gradable shape and the rest of the system can
trust the data.
How it fits: `agent.py` validates every model response against `MatchPrediction`. The eval
harness, store, and dashboard all consume these types.
On camera: "Before writing any agent logic, I defined the contract: given this match info,
return these probabilities. That single decision makes the whole thing testable."
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

Outcome = str  # one of: "home", "draw", "away"


class TeamForm(BaseModel):
    """Recent-form snapshot for one team, assembled by the data tools."""

    name: str
    abbr: str | None = None
    logo: str | None = None
    color: str | None = None
    fifa_rank: int | None = None
    rating: float | None = Field(default=None, description="0-100 strength prior")
    last5: list[str] = Field(default_factory=list, description="Recent results e.g. ['W','D','L']")
    goals_for_avg: float | None = None
    goals_against_avg: float | None = None
    key_absences: list[str] = Field(default_factory=list)


class MatchContext(BaseModel):
    """Everything the agent is told about a single fixture (the agent's input)."""

    match_id: int
    competition: str = "FIFA World Cup 2026"
    stage: str | None = None
    kickoff_utc: datetime | None = None
    home: TeamForm
    away: TeamForm
    head_to_head: list[str] = Field(
        default_factory=list, description="Recent H2H results from home team's perspective"
    )
    venue: str | None = None
    neutral_venue: bool = False
    notes: list[str] = Field(default_factory=list)


class Probabilities(BaseModel):
    """Win/draw/loss probabilities. Must be valid and sum to ~1."""

    home: float = Field(ge=0.0, le=1.0)
    draw: float = Field(ge=0.0, le=1.0)
    away: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_sum(self) -> Probabilities:
        total = self.home + self.draw + self.away
        if abs(total - 1.0) > 0.02:
            raise ValueError(f"probabilities must sum to 1.0 (got {total:.3f})")
        return self

    def normalized(self) -> Probabilities:
        """Return a copy renormalized to sum to exactly 1 (tolerates small model drift)."""
        total = self.home + self.draw + self.away or 1.0
        return Probabilities(
            home=self.home / total, draw=self.draw / total, away=self.away / total
        )

    @property
    def argmax_outcome(self) -> Outcome:
        return max(
            (("home", self.home), ("draw", self.draw), ("away", self.away)),
            key=lambda kv: kv[1],
        )[0]


class MatchPrediction(BaseModel):
    """The agent's structured answer for one match (the agent's output contract)."""

    match_id: int
    probabilities: Probabilities
    predicted_outcome: Outcome
    predicted_score: str | None = Field(default=None, description="e.g. '2-1'")
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(description="Short reasoning the model gives for its pick")

    @field_validator("predicted_outcome")
    @classmethod
    def _valid_outcome(cls, v: str) -> str:
        if v not in {"home", "draw", "away"}:
            raise ValueError("predicted_outcome must be one of home/draw/away")
        return v

    @model_validator(mode="after")
    def _outcome_matches_probs(self) -> MatchPrediction:
        # Keep the headline pick consistent with the probabilities.
        if self.predicted_outcome != self.probabilities.argmax_outcome:
            self.predicted_outcome = self.probabilities.argmax_outcome
        return self


class StoredPrediction(BaseModel):
    """A prediction enriched with metadata for storage, evals, and the dashboard."""

    match_id: int
    model_id: str
    persona: str | None = None
    home_team: str
    away_team: str
    kickoff_utc: datetime | None = None
    prediction: MatchPrediction
    persona_message: str | None = None
    trace_id: str
    created_at: datetime
    # Filled in after the match finishes.
    actual_outcome: Outcome | None = None
    actual_score: str | None = None
