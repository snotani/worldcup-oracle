"""The Oracle agent: the orchestration loop.

What: Ties the pieces together for one prediction: gather data -> build prompt -> call model
-> parse -> validate -> (persona) -> store, emitting a run trace at every step.
Why: This is "the agent." Each step maps directly to the spec and to a video segment, and the
trace makes the whole thing observable.
How it fits: The CLI and FastAPI layer call `predict_match(...)`; the eval harness calls it in
replay mode over historical fixtures.
On camera: "Here's the entire agent loop. Six steps, and you can watch each one happen."
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from .config import Settings, get_settings
from .models import CompletionResult, get_model_backend
from .personas import get_persona
from .schema import MatchContext, MatchPrediction, Probabilities, StoredPrediction
from .store import Store
from .tools import get_provider
from .trace import RunTrace

_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "predict.md"
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text()


def build_match_brief(ctx: MatchContext) -> str:
    """Render the match context as a compact, model-readable brief."""
    brief = {
        "match_id": ctx.match_id,
        "competition": ctx.competition,
        "stage": ctx.stage,
        "kickoff_utc": ctx.kickoff_utc.isoformat() if ctx.kickoff_utc else None,
        "venue": ctx.venue,
        "neutral_venue": ctx.neutral_venue,
        "home": {
            "name": ctx.home.name,
            "strength_rating": ctx.home.rating,
            "last5": ctx.home.last5,
            "goals_for_avg": ctx.home.goals_for_avg,
            "goals_against_avg": ctx.home.goals_against_avg,
            "key_absences": ctx.home.key_absences,
        },
        "away": {
            "name": ctx.away.name,
            "strength_rating": ctx.away.rating,
            "last5": ctx.away.last5,
            "goals_for_avg": ctx.away.goals_for_avg,
            "goals_against_avg": ctx.away.goals_against_avg,
            "key_absences": ctx.away.key_absences,
        },
        "head_to_head_from_home_perspective": ctx.head_to_head,
    }
    return json.dumps(brief, indent=2)


def _apply_temperature(probs: dict[str, float], temperature: float) -> dict[str, float]:
    """Sharpen (T<1) or flatten (T>1) a probability distribution, then renormalize.

    This is standard temperature scaling: p_i^(1/T) / sum_j p_j^(1/T). With T<1 the
    favorite gets more decisive without ever changing the ranking of outcomes.
    """
    if temperature == 1.0 or temperature <= 0:
        return probs
    powered = {k: v ** (1.0 / temperature) for k, v in probs.items()}
    z = sum(powered.values()) or 1.0
    return {k: v / z for k, v in powered.items()}


def parse_prediction(text: str, match_id: int, temperature: float = 1.0) -> MatchPrediction:
    """Extract and validate the JSON prediction from raw model text."""
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError(f"no JSON object found in model output: {text[:200]!r}")
    data = json.loads(match.group(0))
    data["match_id"] = match_id
    # Normalize probabilities so tiny model drift doesn't fail validation, then apply
    # the configured temperature so display and evals share one honest distribution.
    probs = data.get("probabilities", {})
    total = sum(float(probs.get(k, 0)) for k in ("home", "draw", "away")) or 1.0
    norm = {k: float(probs.get(k, 0)) / total for k in ("home", "draw", "away")}
    norm = _apply_temperature(norm, temperature)
    data["probabilities"] = norm
    data["predicted_outcome"] = max(norm.items(), key=lambda kv: kv[1])[0]
    # Confidence always tracks the top probability so the number matches the bars.
    data["confidence"] = max(norm.values())
    data.setdefault("rationale", "")
    return MatchPrediction.model_validate(data)


def advancement(probs: Probabilities) -> tuple[float, float]:
    """Convert 1X2 probabilities into knockout advance probabilities (no draws).

    A knockout has no draw: a level game goes to extra time / penalties. We hand the would-be
    draw mass to each side in proportion to its win probability, which keeps the favourite
    favoured without ever flipping the ranking.
    """
    home, away = probs.home, probs.away
    base = home + away
    if base <= 0:
        return 0.5, 0.5
    home_adv = home + probs.draw * (home / base)
    away_adv = away + probs.draw * (away / base)
    total = home_adv + away_adv or 1.0
    return round(home_adv / total, 4), round(away_adv / total, 4)


def predict_match(
    match_id: int,
    model_id: str | None = None,
    persona: str | None = None,
    *,
    settings: Settings | None = None,
    store: Store | None = None,
    mock_model: bool = False,
    save: bool = True,
) -> tuple[StoredPrediction, RunTrace]:
    """Run the full agent pipeline for one match and return (prediction, trace)."""
    settings = settings or get_settings()
    model_id = model_id or settings.default_model
    trace = RunTrace(label=f"match {match_id}", model_id=model_id)

    provider = get_provider(settings)

    # Step 1: gather data (the agent's tools).
    with trace.step("gather_data", "fetch fixture, form, head-to-head") as s:
        ctx = provider.get_match_context(match_id)
        s.detail(f"{ctx.home.name} vs {ctx.away.name} | form {ctx.home.last5} vs {ctx.away.last5}")
        s.add(home=ctx.home.name, away=ctx.away.name)

    return predict_from_context(
        ctx,
        model_id=model_id,
        persona=persona,
        settings=settings,
        store=store,
        mock_model=mock_model,
        save=save,
        trace=trace,
    )


def predict_from_context(
    ctx: MatchContext,
    model_id: str | None = None,
    persona: str | None = None,
    *,
    settings: Settings | None = None,
    store: Store | None = None,
    mock_model: bool = False,
    save: bool = True,
    trace: RunTrace | None = None,
) -> tuple[StoredPrediction, RunTrace]:
    """Run prompt -> model -> parse -> validate for an already-gathered context.

    Splitting this out lets the bracket simulator predict hypothetical matchups (a future
    quarter-final between two teams that haven't met yet) without a fixture lookup.
    """
    settings = settings or get_settings()
    model_id = model_id or settings.default_model
    match_id = ctx.match_id
    trace = trace or RunTrace(label=f"match {match_id}", model_id=model_id)

    backend = get_model_backend(settings, mock=mock_model)

    # Step 2: build the prompt from the spec template + brief.
    with trace.step("build_prompt", "inject match brief into the prediction prompt") as s:
        prompt = _load_prompt_template().replace("{match_brief}", build_match_brief(ctx))
        if persona:
            prompt += "\n\n" + get_persona(persona).prompt_addon
        s.add(prompt_chars=len(prompt))

    # Step 3: call the model (swap this id for the battle).
    with trace.step("call_model", f"send prompt to {model_id}") as s:
        result: CompletionResult = backend.complete(prompt, model_id, context=ctx)
        s.detail(f"{model_id} -> status {result.status} ({'mock' if result.from_mock else 'live'})")
        s.add(status=result.status, from_mock=result.from_mock, model_ms=result.duration_ms)

    # Step 4 + 5: parse and validate against the contract.
    with trace.step("parse_validate", "extract JSON and validate against schema") as s:
        prediction = parse_prediction(result.text, match_id, temperature=settings.prob_temperature)
        p = prediction.probabilities
        s.detail(
            f"pick={prediction.predicted_outcome} "
            f"(H {p.home:.0%} / D {p.draw:.0%} / A {p.away:.0%})"
        )
        s.add(
            predicted_outcome=prediction.predicted_outcome,
            confidence=prediction.confidence,
        )

    # Step 6 (optional): apply persona voice.
    persona_message = None
    if persona:
        with trace.step("apply_persona", f"render '{persona}' banter") as s:
            persona_message = get_persona(persona).render(prediction, ctx)
            s.detail(persona_message[:80])

    stored = StoredPrediction(
        match_id=match_id,
        model_id=model_id,
        persona=persona,
        home_team=ctx.home.name,
        away_team=ctx.away.name,
        kickoff_utc=ctx.kickoff_utc,
        prediction=prediction,
        persona_message=persona_message,
        trace_id=trace.trace_id,
        created_at=datetime.now(UTC),
    )

    # Step 7: persist prediction + trace.
    if save:
        owns_store = store is None
        store = store or Store()
        try:
            with trace.step("store", "persist prediction and trace") as s:
                store.save_trace(trace.to_dict(), match_id=match_id)
                store.save_prediction(stored)
                s.detail("saved to predictions.db")
        finally:
            if owns_store:
                store.close()

    return stored, trace
