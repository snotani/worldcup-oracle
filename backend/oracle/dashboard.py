"""Builds the data payload the dashboard renders.

What: Assembles one JSON document with everything the two content angles need: the single-agent
bracket simulation (Tab 1) and the five-model bracket battle plus their consensus (Tab 2).
Why: One builder shared by the CLI `export` command (static JSON for a self-contained, easily
recorded dashboard) and the FastAPI server (live).
How it fits: `cli.py export` writes this to `frontend/public/data/dashboard.json`; `api.py`
returns it from an endpoint.
On camera: "Everything you see on the dashboard comes from this one payload the agent produced."

Live model calls are the expensive part: one full bracket is up to 31 predictions, so the
battle is ~31 x len(models). Mock runs are instant.
"""

from __future__ import annotations

from datetime import UTC, datetime

from .config import Settings, get_settings
from .models import BATTLE_REGISTRY
from .simulate import AGENT_FEATURES, simulate_battle, simulate_bracket
from .tools import get_provider


def _resolve_models(friendly: list[str]) -> dict[str, str]:
    """Map friendly battle names to model ids (unknown names pass through as raw ids)."""
    return {name: BATTLE_REGISTRY.get(name, name) for name in friendly}


def _friendly_for(model_id: str) -> str:
    """Reverse-lookup the friendly battle name for a model id (else the id itself)."""
    for name, mid in BATTLE_REGISTRY.items():
        if mid == model_id:
            return name
    return model_id


def build_payload(
    *,
    settings: Settings | None = None,
    mock_model: bool = False,
    battle: list[str] | None = None,
    **_ignored,
) -> dict:
    """Run the bracket simulations and assemble the dashboard payload."""
    settings = settings or get_settings()
    offline = mock_model or settings.use_mock_data
    provider = None if offline else get_provider(settings)

    names = battle or list(BATTLE_REGISTRY.keys())
    models = _resolve_models(names)

    # Tab 2: every model plays the whole bracket; consensus compares them.
    result = simulate_battle(models, settings=settings, mock_model=mock_model, provider=provider)
    brackets = result["brackets"]

    # Tab 1: the single "Oracle" agent. Reuse the default model's bracket if it's already in the
    # battle (saves a full re-run on live), else simulate it on its own.
    default_id = settings.default_model
    simulation = next((b for b in brackets if b["model_id"] == default_id), None)
    if simulation is None:
        simulation = simulate_bracket(
            default_id, model_name=_friendly_for(default_id),
            settings=settings, mock_model=mock_model, provider=provider,
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "mock": offline,
        "competition": "FIFA World Cup 2026",
        "agent_features": AGENT_FEATURES,
        "simulation": simulation,
        "model_brackets": brackets,
        "consensus": result["consensus"],
        "models": [{"name": n, "model_id": m} for n, m in models.items()],
    }
