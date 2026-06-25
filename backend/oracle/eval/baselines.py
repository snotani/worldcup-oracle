"""Baselines: the bar the agent has to beat.

What: Simple, model-free predictors (uniform coin-flip, home-advantage prior, recent-form
model) that produce probabilities from the same match context.
Why: "64% accuracy" means nothing without a baseline. Beating a coin flip is the minimum;
beating a sensible form model is the real test (and the bookies-style comparison).
How it fits: `backtest.py` scores the agent against every baseline on the same fixtures.
On camera: "If the AI can't beat a coin flip and a simple form model, it's not earning its
keep. So we put them all on the same scoreboard."
"""

from __future__ import annotations

from collections.abc import Callable

from ..schema import MatchContext

Probs = dict[str, float]


def _normalize(home: float, draw: float, away: float) -> Probs:
    total = home + draw + away or 1.0
    return {"home": home / total, "draw": draw / total, "away": away / total}


def uniform(_ctx: MatchContext) -> Probs:
    """Coin flip: every outcome equally likely."""
    return {"home": 1 / 3, "draw": 1 / 3, "away": 1 / 3}


def home_advantage(_ctx: MatchContext) -> Probs:
    """Fixed prior reflecting the historical edge of the first-named team."""
    return _normalize(0.45, 0.27, 0.28)


def _form_points(last5: list[str]) -> float:
    return sum({"W": 3.0, "D": 1.0, "L": 0.0}.get(r, 0.0) for r in last5)


def form_model(ctx: MatchContext) -> Probs:
    """A respectable non-AI predictor based on recent form + home advantage."""
    home_pts = _form_points(ctx.home.last5) + 2.0  # home advantage
    away_pts = _form_points(ctx.away.last5)
    spread = home_pts - away_pts
    # Map the points spread to outcome probabilities with a draw mass in the middle.
    home = 0.33 + 0.03 * spread
    away = 0.33 - 0.03 * spread
    draw = 1.0 - home - away
    home = min(0.85, max(0.05, home))
    away = min(0.85, max(0.05, away))
    draw = max(0.05, draw)
    return _normalize(home, draw, away)


BASELINES: dict[str, Callable[[MatchContext], Probs]] = {
    "coin_flip": uniform,
    "home_prior": home_advantage,
    "form_model": form_model,
}


def all_baselines(ctx: MatchContext) -> dict[str, Probs]:
    """Return every baseline's probabilities for a single match."""
    return {name: fn(ctx) for name, fn in BASELINES.items()}
