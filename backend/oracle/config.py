"""Configuration and credentials.

What: Loads runtime settings and API keys from environment / .env files.
Why: One typed place for credentials and paths so no module reads os.environ ad hoc.
How it fits: Every other module imports `get_settings()` to find keys, data dirs, and the
default model. The keys themselves (CURSOR_API_KEY, API_FOOTBALL_KEY) live in the repo-root
.env and are never committed.
On camera: "This is where the agent gets its two keys: one for the Cursor models, one for the
football data."
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ -> worldcup-oracle/ -> repo root. We search every level for a .env so the same
# config works whether you run from the repo root or from inside backend/.
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_PROJECT_DIR = _BACKEND_DIR.parent
_REPO_ROOT = _PROJECT_DIR.parent

_ENV_FILES = [
    _REPO_ROOT / ".env",
    _PROJECT_DIR / ".env",
    _BACKEND_DIR / ".env",
]

DATA_DIR = _BACKEND_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
HISTORICAL_DIR = DATA_DIR / "historical"
PREDICTIONS_DB = DATA_DIR / "predictions.db"


class Settings(BaseSettings):
    """Typed view of everything the agent needs to run."""

    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_FILES],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cursor_api_key: str | None = None
    api_football_key: str | None = None

    # Live data source: "espn" (free, real 2026, default), "api_football", or "mock".
    data_source: str = "espn"

    # ESPN public API (no key) - FIFA World Cup. Window spans the tournament.
    espn_league: str = "fifa.world"
    espn_window: str = "20260601-20260731"

    # World Cup in API-Football (free tier covers 2022-2024 only).
    wc_league_id: int = 1
    wc_season: int = 2026

    # Default model id for single predictions; the battle overrides this per run.
    default_model: str = "composer-2.5"

    # Probability "temperature" applied to the model's 1X2 distribution before scoring.
    # 1.0 = use the model's raw output. <1.0 sharpens it (more decisive favorites);
    # >1.0 flattens it. Applied consistently to display AND evals so nothing is gamed.
    prob_temperature: float = 0.7

    # When True (or when API_FOOTBALL_KEY is missing) the data layer serves bundled
    # mock fixtures instead of hitting the network. Keeps tests and demos offline.
    use_mock_data: bool = False

    @property
    def has_cursor_key(self) -> bool:
        return bool(self.cursor_api_key)

    @property
    def has_football_key(self) -> bool:
        return bool(self.api_football_key)


@lru_cache
def get_settings() -> Settings:
    """Return process-wide settings (cached so .env is read once)."""
    return Settings()
