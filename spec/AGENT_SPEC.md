# Agent Spec — The Oracle

This document is written *before* the code. It defines the agent's contract so the
implementation has something concrete to satisfy. (Spec-driven development.)

## 1. Problem / use case

Football fans, pundits, and bookmakers all try to predict match outcomes. Can a simple,
transparent AI agent — given only pre-match information — predict FIFA World Cup 2026 results
as well as (or better than) naive baselines, and do it in a way that is fully explainable?

The agent must be:

- **Honest**: only uses information available before kickoff (no leakage).
- **Calibrated**: outputs probabilities, not just a pick.
- **Explainable**: every step it takes is observable and recordable.
- **Modular**: the same core supports three content angles (accuracy, model battle, persona).

## 2. Inputs

The agent receives a `MatchContext` (see `backend/oracle/schema.py`):

- `match_id`, `competition`, `stage`, `kickoff_utc`, `venue`
- `home` / `away` `TeamForm`: name, last-5 results, goals-for/against averages, key absences
- `head_to_head`: recent results from the home team's perspective

These are assembled by the data tools (`backend/oracle/tools/api_football.py`) from
API-Football, or from bundled mock data when offline.

## 3. Output (the contract)

The agent must return a `MatchPrediction`:

```json
{
  "match_id": 1001,
  "probabilities": {"home": 0.45, "draw": 0.27, "away": 0.28},
  "predicted_outcome": "home",
  "predicted_score": "2-1",
  "confidence": 0.45,
  "rationale": "short reasoning"
}
```

Invariants (enforced in `schema.py`):

- `probabilities` are each in `[0, 1]` and sum to `1.0` (±0.02 tolerance, then renormalized).
- `predicted_outcome` equals the argmax of `probabilities`.
- `confidence` equals the top probability.

## 4. Tools

The agent's "tools" are data-gathering functions, not free-form actions:

- `get_match_context(match_id)` — fixture + both teams' form + head-to-head.
- `list_fixtures(status)` — upcoming (`NS`) or finished (`FT`) fixtures.
- `get_result(match_id)` — actual outcome for a finished match (used only for evaluation).

Caching (`tools/cache.py`) keeps us under API-Football's ~100 req/day free tier.

## 5. Model

Models are called through the Cursor Agent SDK (`backend/oracle/models.py`). The model id is a
single swappable parameter — this is what makes the Model Battle (Angle B) a one-line change.
A deterministic mock backend produces valid JSON offline for tests and demos.

The agent runs the model read-only with a strict "return JSON only, do not modify files"
instruction (`backend/oracle/prompts/predict.md`).

## 6. Guardrails

- Output is parsed defensively (JSON extracted from any surrounding text) and validated against
  the schema; invalid probabilities are renormalized rather than trusted blindly.
- The model runs in a sandbox working directory; it is not allowed to act on the repo.
- No betting/odds/money framing — accuracy comparison only.

## 7. Success criteria

The agent is considered successful if, over a backtest of finished matches, it:

1. Beats the coin-flip baseline on accuracy, **and**
2. Beats or matches the recent-form model on Brier score (calibration).

See `EVAL_SPEC.md` for how this is measured.

## 8. Pipeline (what "the agent" does per prediction)

1. `gather_data` — call the tools to build the `MatchContext`.
2. `build_prompt` — inject the brief into the spec prompt (+ persona addon if any).
3. `call_model` — send to the chosen model via the Cursor SDK.
4. `parse_validate` — extract JSON, validate against the contract.
5. `apply_persona` (optional) — wrap the result in a character voice.
6. `store` — persist the prediction and the run trace.

Every step is emitted to a `RunTrace` (`backend/oracle/trace.py`) so it can be shown on camera.
