"""Evaluation harness: how we prove the agent is actually any good."""

from .backtest import BacktestReport, run_backtest, score_stored_predictions
from .metrics import EvalSample, MetricSummary, summarize

__all__ = [
    "BacktestReport",
    "EvalSample",
    "MetricSummary",
    "run_backtest",
    "score_stored_predictions",
    "summarize",
]
