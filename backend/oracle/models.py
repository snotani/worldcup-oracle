"""Model backend: how the agent talks to an LLM (via the Cursor Agent SDK).

What: A thin adapter over the Cursor Agent SDK that sends a prompt to a chosen model and
returns the final text. Also a deterministic mock backend for offline runs/tests.
Why: Keeping the model behind one interface is what makes the "Model Battle" (Angle B) a
one-line change (swap model_id) and lets us swap to OpenRouter/BYOK later without touching
the agent.
How it fits: `agent.py` calls `backend.complete(prompt, model_id)`. `Cursor.models.list()`
discovers which model ids your account can use.
On camera: "The agent doesn't care which model it is. I just change this one id, and now it's
Claude instead of GPT, same spec, same prompt - that's the whole battle."
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import DATA_DIR, Settings, get_settings

if TYPE_CHECKING:
    from .schema import MatchContext

# Friendly names -> Cursor model ids used for the battle. Verify/adjust against
# `Cursor.models.list()` for your account; ids evolve.
BATTLE_REGISTRY: dict[str, str] = {
    "claude": "claude-sonnet-4-6",
    "gpt": "gpt-5.5",
    "gemini": "gemini-3.1-pro",
    "grok": "grok-4.3",
    "composer": "composer-2.5",
}

_SANDBOX = DATA_DIR / "sandbox"


@dataclass
class CompletionResult:
    """The outcome of one model call."""

    text: str
    model_id: str
    status: str  # "finished" | "error" | ...
    duration_ms: float
    from_mock: bool = False


class ModelError(RuntimeError):
    """Raised when a model call cannot start or fails."""


class CursorModelBackend:
    """Runs prompts through the Cursor Agent SDK (read-only, JSON-only)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.has_cursor_key:
            raise ModelError("CURSOR_API_KEY is not set; cannot use the Cursor model backend.")
        _SANDBOX.mkdir(parents=True, exist_ok=True)

    def list_available_models(self) -> list[str]:
        """Return model ids the account can use (best-effort)."""
        try:
            from cursor_sdk import Cursor
        except ImportError as exc:  # pragma: no cover
            raise ModelError("cursor-sdk is not installed (pip install cursor-sdk).") from exc
        # Our keys live in .env (loaded into Settings), not the process env, so pass it.
        try:
            models = Cursor.models.list(api_key=self.settings.cursor_api_key)
        except TypeError:
            models = Cursor.models.list()
        return [getattr(m, "id", str(m)) for m in models]

    def complete(
        self, prompt: str, model_id: str, context: MatchContext | None = None
    ) -> CompletionResult:
        import time

        try:
            from cursor_sdk import (
                Agent,
                AgentOptions,
                CursorAgentError,
                LocalAgentOptions,
            )
        except ImportError as exc:  # pragma: no cover
            raise ModelError("cursor-sdk is not installed (pip install cursor-sdk).") from exc

        start = time.perf_counter()
        try:
            result = Agent.prompt(
                prompt,
                AgentOptions(
                    api_key=self.settings.cursor_api_key,
                    model=model_id,
                    local=LocalAgentOptions(cwd=str(_SANDBOX)),
                ),
            )
        except CursorAgentError as exc:
            raise ModelError(f"model run did not start: {exc}") from exc
        duration = round((time.perf_counter() - start) * 1000, 1)
        if result.status != "finished":
            raise ModelError(f"model run ended with status={result.status}")
        return CompletionResult(
            text=result.result or "",
            model_id=model_id,
            status=result.status,
            duration_ms=duration,
        )


class MockModelBackend:
    """Deterministic offline backend: derives plausible JSON from the match context.

    Lets the entire agent pipeline (prompt -> parse -> validate -> store -> eval) run with no
    network, no key, and no Cursor usage. Different model ids get slightly different numbers so
    the battle is visibly a battle.
    """

    @staticmethod
    def list_available_models() -> list[str]:
        return list(BATTLE_REGISTRY.values())

    def complete(
        self, prompt: str, model_id: str, context: MatchContext | None = None
    ) -> CompletionResult:
        import time

        start = time.perf_counter()
        payload = self._heuristic_prediction(model_id, context)
        text = json.dumps(payload)
        return CompletionResult(
            text=text,
            model_id=model_id,
            status="finished",
            duration_ms=round((time.perf_counter() - start) * 1000, 1),
            from_mock=True,
        )

    def _heuristic_prediction(self, model_id: str, context: MatchContext | None) -> dict:
        if context is None:
            base_home, base_draw, base_away = 0.4, 0.3, 0.3
            home_name, away_name = "Home", "Away"
        else:
            home_name, away_name = context.home.name, context.away.name
            # Strength rating dominates, recent form + home edge + H2H modulate. A 0-100
            # rating maps to ~0-7 points so a clear quality gap shows up as a clear favourite.
            # Knockouts are at neutral venues, so the first-named edge nearly vanishes.
            home_edge = 0.15 if context.neutral_venue else 1.0
            home_pts = (context.home.rating or 70) / 14.0 + home_edge
            away_pts = (context.away.rating or 70) / 14.0
            home_pts += _form_points(context.home.last5) / 3.0
            away_pts += _form_points(context.away.last5) / 3.0
            home_pts += _h2h_bias(context.head_to_head)
            total = home_pts + away_pts + 3.0
            base_home = home_pts / total
            base_away = away_pts / total
            base_draw = max(0.12, 1.0 - base_home - base_away)
        # Per-model perturbation so models disagree a little.
        jitter = (int(hashlib.sha256(model_id.encode()).hexdigest(), 16) % 11 - 5) / 100.0
        home = max(0.05, base_home + jitter)
        away = max(0.05, base_away - jitter / 2)
        draw = max(0.05, base_draw - jitter / 2)
        total = home + draw + away
        home, draw, away = home / total, draw / total, away / total
        outcome = max((("home", home), ("draw", draw), ("away", away)), key=lambda kv: kv[1])[0]
        winner = home_name if outcome == "home" else (away_name if outcome == "away" else "either")
        return {
            "probabilities": {
                "home": round(home, 3),
                "draw": round(draw, 3),
                "away": round(away, 3),
            },
            "predicted_outcome": outcome,
            "predicted_score": "2-1" if outcome != "draw" else "1-1",
            "confidence": round(max(home, draw, away), 3),
            "rationale": (
                f"[offline heuristic] {home_name} vs {away_name}: leaning {winner} on recent "
                f"form and home advantage."
            ),
        }


def _form_points(last5: list[str]) -> float:
    return sum({"W": 3, "D": 1, "L": 0}.get(r, 0) for r in last5)


def _h2h_bias(h2h: list[str]) -> float:
    return 0.4 * sum({"W": 1, "D": 0, "L": -1}.get(r, 0) for r in h2h)


def get_model_backend(settings: Settings | None = None, mock: bool = False):
    """Return a Cursor backend, or the mock backend when requested or no key is present."""
    settings = settings or get_settings()
    if mock or settings.use_mock_data or not settings.has_cursor_key:
        return MockModelBackend()
    return CursorModelBackend(settings)
