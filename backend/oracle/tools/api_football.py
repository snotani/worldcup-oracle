"""Data provider: API-Football (api-sports.io) client + offline mock.

What: Fetches World Cup 2026 fixtures, recent team form, and head-to-head records, then
assembles them into the `MatchContext` the agent reasons over.
Why: An agent is only as good as the context it's given. This is the "tools" layer that turns
raw API JSON into a clean, typed brief for the model.
How it fits: `agent.py` calls `get_provider().get_match_context(match_id)`; the result goes
straight into the prompt. Caching (tools/cache.py) keeps us under the free-tier quota.
On camera: "Before predicting, the agent pulls each team's last five results and their head to
head record. Same data a human analyst would want."
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from ..config import Settings, get_settings
from ..schema import MatchContext, TeamForm
from .cache import FileCache

API_BASE = "https://v3.football.api-sports.io"
_MOCK_FILE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "mock_data.json"


def _outcome_from_goals(home_goals: int | None, away_goals: int | None) -> str | None:
    if home_goals is None or away_goals is None:
        return None
    if home_goals > away_goals:
        return "home"
    if home_goals < away_goals:
        return "away"
    return "draw"


def _result_letter(team_id: int, fx: dict[str, Any]) -> str:
    """W/D/L for `team_id` given a raw API-Football fixture row."""
    teams = fx.get("teams", {})
    goals = fx.get("goals", {})
    home_id = teams.get("home", {}).get("id")
    hg, ag = goals.get("home"), goals.get("away")
    outcome = _outcome_from_goals(hg, ag)
    if outcome is None:
        return "?"
    if outcome == "draw":
        return "D"
    won_home = outcome == "home"
    is_home = team_id == home_id
    return "W" if (won_home == is_home) else "L"


class DataProvider:
    """Builds MatchContext objects from API-Football data (live or mocked)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.cache = FileCache()

    # --- raw access (overridden by the mock) -------------------------------------------

    def _get(self, endpoint: str, params: dict[str, Any], ttl: int = 6 * 60 * 60) -> list[dict]:
        """GET an API-Football endpoint and return its `response` array (cached)."""

        def fetch() -> list[dict]:
            headers = {"x-apisports-key": self.settings.api_football_key or ""}
            resp = httpx.get(
                f"{API_BASE}/{endpoint}", params=params, headers=headers, timeout=30
            )
            resp.raise_for_status()
            body = resp.json()
            return body.get("response", [])

        value, _from_cache = self.cache.get_or_fetch(endpoint, params, fetch, ttl_seconds=ttl)
        return value

    # --- public API --------------------------------------------------------------------

    def list_fixtures(self, status: str | None = None) -> list[dict[str, Any]]:
        """Return simplified fixtures for the tournament, optionally filtered by status.

        status: "NS" (not started) or "FT" (finished) or None (all).
        """
        params = {"league": self.settings.wc_league_id, "season": self.settings.wc_season}
        raw = self._get("fixtures", params, ttl=60 * 60)
        out = [self._simplify_fixture(fx) for fx in raw]
        if status == "NS":
            out = [f for f in out if f["status"] in {"NS", "TBD"}]
        elif status == "FT":
            out = [f for f in out if f["status"] in {"FT", "AET", "PEN"}]
        return out

    def get_match_context(self, match_id: int) -> MatchContext:
        """Assemble the full brief the agent reasons over for one fixture."""
        fx = self._find_fixture(match_id)
        if fx is None:
            raise ValueError(f"fixture {match_id} not found for season {self.settings.wc_season}")
        home_id = fx["teams"]["home"]["id"]
        away_id = fx["teams"]["away"]["id"]
        before = fx.get("fixture", {}).get("date")
        home = self._team_form(home_id, fx["teams"]["home"]["name"], before_date=before)
        away = self._team_form(away_id, fx["teams"]["away"]["name"], before_date=before)
        h2h = self._head_to_head(home_id, away_id, before_date=before)
        return MatchContext(
            match_id=match_id,
            stage=fx.get("league", {}).get("round"),
            kickoff_utc=fx.get("fixture", {}).get("date"),
            home=home,
            away=away,
            head_to_head=h2h,
            venue=(fx.get("fixture", {}).get("venue", {}) or {}).get("name"),
        )

    def get_result(self, match_id: int) -> tuple[str, str] | None:
        """Return (outcome, 'h-a') for a finished match, else None."""
        fx = self._find_fixture(match_id)
        if fx is None:
            return None
        status = fx.get("fixture", {}).get("status", {}).get("short")
        if status not in {"FT", "AET", "PEN"}:
            return None
        hg = fx.get("goals", {}).get("home")
        ag = fx.get("goals", {}).get("away")
        outcome = _outcome_from_goals(hg, ag)
        if outcome is None:
            return None
        return outcome, f"{hg}-{ag}"

    # --- helpers -----------------------------------------------------------------------

    def _simplify_fixture(self, fx: dict[str, Any]) -> dict[str, Any]:
        return {
            "match_id": fx.get("fixture", {}).get("id"),
            "status": fx.get("fixture", {}).get("status", {}).get("short"),
            "kickoff_utc": fx.get("fixture", {}).get("date"),
            "stage": fx.get("league", {}).get("round"),
            "home_team": fx.get("teams", {}).get("home", {}).get("name"),
            "away_team": fx.get("teams", {}).get("away", {}).get("name"),
            "home_goals": fx.get("goals", {}).get("home"),
            "away_goals": fx.get("goals", {}).get("away"),
        }

    def _all_raw_fixtures(self) -> list[dict[str, Any]]:
        """All raw fixtures for the tournament (cached); reused for form + H2H."""
        return self._get(
            "fixtures",
            {"league": self.settings.wc_league_id, "season": self.settings.wc_season},
            ttl=60 * 60,
        )

    def _team_matches_before(self, team_id: int, before_date: str | None) -> list[dict[str, Any]]:
        """Finished tournament matches for a team strictly before a date (no leakage)."""
        out = []
        for fx in self._all_raw_fixtures():
            status = fx.get("fixture", {}).get("status", {}).get("short")
            if status not in {"FT", "AET", "PEN"}:
                continue
            date = fx.get("fixture", {}).get("date")
            if before_date and date and date >= before_date:
                continue
            teams = fx.get("teams", {})
            if team_id in (teams.get("home", {}).get("id"), teams.get("away", {}).get("id")):
                out.append(fx)
        out.sort(key=lambda f: f.get("fixture", {}).get("date") or "")
        return out

    def _find_fixture(self, match_id: int) -> dict[str, Any] | None:
        raw = self._all_raw_fixtures()
        for fx in raw:
            if fx.get("fixture", {}).get("id") == match_id:
                return fx
        # Fall back to a direct id lookup (covers fixtures outside the cached page).
        direct = self._get("fixtures", {"id": match_id}, ttl=60 * 60)
        return direct[0] if direct else None

    def _team_form(self, team_id: int, name: str, before_date: str | None = None) -> TeamForm:
        # Prefer real in-tournament history (free, no plan limit); fall back to the last-5 endpoint.
        raw = self._team_matches_before(team_id, before_date)[-5:]
        if not raw:
            raw = self._get("fixtures", {"team": team_id, "last": 5}, ttl=12 * 60 * 60)
        last5: list[str] = []
        gf: list[int] = []
        ga: list[int] = []
        for fx in raw:
            last5.append(_result_letter(team_id, fx))
            teams = fx.get("teams", {})
            goals = fx.get("goals", {})
            is_home = teams.get("home", {}).get("id") == team_id
            scored = goals.get("home") if is_home else goals.get("away")
            conceded = goals.get("away") if is_home else goals.get("home")
            if scored is not None:
                gf.append(scored)
            if conceded is not None:
                ga.append(conceded)
        return TeamForm(
            name=name,
            last5=last5,
            goals_for_avg=round(sum(gf) / len(gf), 2) if gf else None,
            goals_against_avg=round(sum(ga) / len(ga), 2) if ga else None,
        )

    def _head_to_head(
        self, home_id: int, away_id: int, before_date: str | None = None
    ) -> list[str]:
        # In-tournament H2H from cached fixtures; fall back to the dedicated endpoint.
        raw = [
            fx
            for fx in self._team_matches_before(home_id, before_date)
            if away_id
            in (
                fx.get("teams", {}).get("home", {}).get("id"),
                fx.get("teams", {}).get("away", {}).get("id"),
            )
        ]
        if not raw:
            raw = self._get(
                "fixtures/headtohead", {"h2h": f"{home_id}-{away_id}", "last": 5}, ttl=24 * 60 * 60
            )
        return [_result_letter(home_id, fx) for fx in raw]


class MockProvider(DataProvider):
    """Offline provider that serves bundled JSON so demos/tests need no network or key."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings)
        self._data = json.loads(_MOCK_FILE.read_text())

    def _get(self, endpoint: str, params: dict[str, Any], ttl: int = 0) -> list[dict]:
        if endpoint == "fixtures" and "team" in params:
            return self._data.get("team_form", {}).get(str(params["team"]), [])
        if endpoint == "fixtures/headtohead":
            return self._data.get("head_to_head", {}).get(params.get("h2h", ""), [])
        if endpoint == "fixtures" and "id" in params:
            return [f for f in self._data.get("fixtures", []) if
                    f.get("fixture", {}).get("id") == params["id"]]
        if endpoint == "fixtures":
            return self._data.get("fixtures", [])
        return []


def get_provider(settings: Settings | None = None):
    """Return the configured data provider.

    - mock when use_mock_data is set (offline)
    - api_football when DATA_SOURCE=api_football and a key is present
    - espn otherwise (default; free, live 2026 World Cup)
    """
    settings = settings or get_settings()
    if settings.use_mock_data:
        return MockProvider(settings)
    if settings.data_source == "api_football":
        if not settings.has_football_key:
            return MockProvider(settings)
        return DataProvider(settings)
    # Default: ESPN public API (no key, real 2026 data).
    from .espn import EspnProvider

    return EspnProvider(settings)
