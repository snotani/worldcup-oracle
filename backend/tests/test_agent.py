"""End-to-end pipeline tests using the offline mock data + mock model."""

from __future__ import annotations

from oracle.agent import parse_prediction, predict_match
from oracle.config import Settings


def _mock_settings() -> Settings:
    return Settings(use_mock_data=True, default_model="composer-2.5")


def test_predict_match_offline_produces_valid_prediction() -> None:
    settings = _mock_settings()
    stored, trace = predict_match(
        1001, model_id="composer-2.5", settings=settings, mock_model=True, save=False
    )
    p = stored.prediction.probabilities
    assert abs((p.home + p.draw + p.away) - 1.0) < 1e-6
    assert stored.prediction.predicted_outcome in {"home", "draw", "away"}
    assert stored.home_team == "Brazil"
    assert stored.away_team == "Argentina"
    # The trace should capture the full pipeline.
    step_names = [s.name for s in trace.steps]
    assert step_names[:4] == ["gather_data", "build_prompt", "call_model", "parse_validate"]


def test_persona_adds_message() -> None:
    settings = _mock_settings()
    stored, _ = predict_match(
        1001, model_id="composer-2.5", persona="gaffer", settings=settings,
        mock_model=True, save=False,
    )
    assert stored.persona == "gaffer"
    assert stored.persona_message


def test_battle_models_can_disagree_or_agree_but_stay_valid() -> None:
    settings = _mock_settings()
    outcomes = set()
    for model_id in ["claude-x", "gpt-x", "gemini-x"]:
        stored, _ = predict_match(
            1001, model_id=model_id, settings=settings, mock_model=True, save=False
        )
        outcomes.add(stored.prediction.predicted_outcome)
        assert stored.model_id == model_id
    assert outcomes  # at least one outcome produced


def test_parse_prediction_handles_code_fences() -> None:
    raw = """Here you go:
    ```json
    {"probabilities": {"home": 0.5, "draw": 0.3, "away": 0.2},
     "predicted_outcome": "home", "predicted_score": "2-1",
     "confidence": 0.5, "rationale": "ok"}
    ```"""
    pred = parse_prediction(raw, match_id=42)
    assert pred.match_id == 42
    assert pred.predicted_outcome == "home"
