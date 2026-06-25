"""Unit tests for the evaluation metrics and backtest."""

from __future__ import annotations

from oracle.config import Settings
from oracle.eval.backtest import run_backtest
from oracle.eval.metrics import EvalSample, accuracy, brier_score, log_loss


def _samples() -> list[EvalSample]:
    return [
        EvalSample(probs={"home": 0.7, "draw": 0.2, "away": 0.1}, predicted="home", actual="home"),
        EvalSample(probs={"home": 0.2, "draw": 0.3, "away": 0.5}, predicted="away", actual="home"),
    ]


def test_accuracy() -> None:
    assert accuracy(_samples()) == 0.5


def test_brier_is_lower_for_confident_correct() -> None:
    good = [EvalSample({"home": 0.9, "draw": 0.05, "away": 0.05}, "home", "home")]
    bad = [EvalSample({"home": 0.1, "draw": 0.05, "away": 0.85}, "away", "home")]
    assert brier_score(good) < brier_score(bad)


def test_log_loss_penalizes_wrong_confident() -> None:
    bad = [EvalSample({"home": 0.01, "draw": 0.01, "away": 0.98}, "away", "home")]
    assert log_loss(bad) > 1.0


def test_backtest_runs_offline() -> None:
    settings = Settings(use_mock_data=True, default_model="composer-2.5")
    report = run_backtest("composer-2.5", settings=settings, mock_model=True)
    assert report.n_matches >= 1
    names = {s.name for s in report.summaries}
    assert "agent:composer-2.5" in names
    assert "coin_flip" in names
