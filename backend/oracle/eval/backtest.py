"""Backtest: run the agent over finished matches and score it vs baselines.

What: For every completed World Cup fixture, generate the agent's prediction and each
baseline's prediction, compare to the real result, and summarize the metrics.
Why: This is the "evals + results" phase of the lifecycle. It produces the scoreboard that
powers Angle A and validates the agent before the live tournament.
How it fits: The CLI `eval` command and the FastAPI layer call `run_backtest(...)`. Live
results are scored separately via `score_stored_predictions(...)`.
On camera: "We replay the agent over matches we already know the result of. No cheating - it
only sees pre-match info - and we see exactly how good it is."
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..agent import predict_match
from ..config import Settings, get_settings
from ..schema import StoredPrediction
from ..store import Store
from ..tools import get_provider
from .baselines import all_baselines
from .metrics import EvalSample, MetricSummary, summarize


@dataclass
class BacktestReport:
    """Everything a backtest produces."""

    model_id: str
    n_matches: int
    summaries: list[MetricSummary]
    rows: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "n_matches": self.n_matches,
            "summaries": [s.to_dict() for s in self.summaries],
            "rows": self.rows,
        }


def run_backtest(
    model_id: str | None = None,
    *,
    settings: Settings | None = None,
    mock_model: bool = False,
    limit: int | None = None,
) -> BacktestReport:
    """Score the agent and all baselines over finished fixtures."""
    settings = settings or get_settings()
    model_id = model_id or settings.default_model
    provider = get_provider(settings)

    finished = provider.list_fixtures(status="FT")
    if limit:
        finished = finished[:limit]

    agent_samples: list[EvalSample] = []
    baseline_samples: dict[str, list[EvalSample]] = {}
    rows: list[dict] = []

    for fx in finished:
        match_id = fx["match_id"]
        result = provider.get_result(match_id)
        if result is None:
            continue
        actual_outcome, actual_score = result
        ctx = provider.get_match_context(match_id)

        stored, _trace = predict_match(
            match_id,
            model_id=model_id,
            settings=settings,
            mock_model=mock_model,
            save=False,
        )
        p = stored.prediction.probabilities
        agent_samples.append(
            EvalSample(
                probs={"home": p.home, "draw": p.draw, "away": p.away},
                predicted=stored.prediction.predicted_outcome,
                actual=actual_outcome,
            )
        )

        for name, probs in all_baselines(ctx).items():
            predicted = max(probs.items(), key=lambda kv: kv[1])[0]
            baseline_samples.setdefault(name, []).append(
                EvalSample(probs=probs, predicted=predicted, actual=actual_outcome)
            )

        rows.append(
            {
                "match_id": match_id,
                "home_team": fx["home_team"],
                "away_team": fx["away_team"],
                "actual_outcome": actual_outcome,
                "actual_score": actual_score,
                "agent_pick": stored.prediction.predicted_outcome,
                "agent_correct": stored.prediction.predicted_outcome == actual_outcome,
                "agent_probs": {"home": p.home, "draw": p.draw, "away": p.away},
            }
        )

    summaries = [summarize(f"agent:{model_id}", agent_samples)]
    for name, samples in baseline_samples.items():
        summaries.append(summarize(name, samples))

    return BacktestReport(
        model_id=model_id,
        n_matches=len(rows),
        summaries=summaries,
        rows=rows,
    )


def _samples_from_stored(preds: list[StoredPrediction]) -> list[EvalSample]:
    out: list[EvalSample] = []
    for sp in preds:
        if sp.actual_outcome is None:
            continue
        p = sp.prediction.probabilities
        out.append(
            EvalSample(
                probs={"home": p.home, "draw": p.draw, "away": p.away},
                predicted=sp.prediction.predicted_outcome,
                actual=sp.actual_outcome,
            )
        )
    return out


def score_stored_predictions(store: Store | None = None) -> list[MetricSummary]:
    """Score the real, stored predictions (those whose matches have finished) per model."""
    owns = store is None
    store = store or Store()
    try:
        summaries: list[MetricSummary] = []
        for model_id in store.distinct_models():
            preds = [
                sp
                for sp in store.predictions(model_id=model_id, only_completed=True)
                if sp.persona is None
            ]
            samples = _samples_from_stored(preds)
            if samples:
                summaries.append(summarize(f"agent:{model_id}", samples))
        return summaries
    finally:
        if owns:
            store.close()
