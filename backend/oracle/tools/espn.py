"""Data provider: ESPN public soccer API (live FIFA World Cup 2026, no key).

What: Fetches the whole tournament's fixtures, form, and results from ESPN's free public
endpoint and assembles them into the agent's `MatchContext`.
Why: API-Football's free tier doesn't include season 2026; ESPN's public API does, with no key
and a prebuilt recent-form string per team. One request covers the entire tournament.
How it fits: Drop-in alternative to the API-Football `DataProvider`, selected by
`DATA_SOURCE=espn` (the default for live runs).
On camera: "This pulls the actual, current World Cup - every match, live - straight from ESPN."
"""

from __future__ import annotations

from typing import Any

import httpx

from ..config import Settings, get_settings
from ..schema import MatchContext, TeamForm
from .cache import FileCache

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

# ESPN event state -> our status codes.
_STATE_TO_STATUS = {"pre": "NS", "in": "LIVE", "post": "FT"}


def _outcome(home_goals: int | None, away_goals: int | None) -> str | None:
    if home_goals is None or away_goals is None:
        return None
    if home_goals > away_goals:
        return "home"
    if home_goals < away_goals:
        return "away"
    return "draw"


class EspnProvider:
    """Builds MatchContext objects from ESPN's World Cup scoreboard."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.cache = FileCache()
        self.league = self.settings.espn_league
        self.window = self.settings.espn_window

    # --- raw access --------------------------------------------------------------------

    def _events(self) -> list[dict[str, Any]]:
        """All tournament events (cached); a single ESPN request covers everything."""
        params = {"league": self.league, "dates": self.window}

        def fetch() -> list[dict[str, Any]]:
            url = f"{ESPN_BASE}/{self.league}/scoreboard"
            resp = httpx.get(url, params={"dates": self.window}, timeout=30)
            resp.raise_for_status()
            return resp.json().get("events", [])

        value, _ = self.cache.get_or_fetch("espn_scoreboard", params, fetch, ttl_seconds=15 * 60)
        return value

    @staticmethod
    def _sides(event: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        comp = event["competitions"][0]
        home = away = {}
        for c in comp["competitors"]:
            if c.get("homeAway") == "home":
                home = c
            else:
                away = c
        return home, away

    @staticmethod
    def _score(competitor: dict[str, Any]) -> int | None:
        raw = competitor.get("score")
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def _find_event(self, match_id: int) -> dict[str, Any] | None:
        for e in self._events():
            if str(e.get("id")) == str(match_id):
                return e
        return None

    @staticmethod
    def _team_meta(competitor: dict[str, Any]) -> dict[str, Any]:
        t = competitor.get("team", {})
        color = t.get("color")
        return {
            "name": t.get("displayName"),
            "abbr": t.get("abbreviation"),
            "logo": t.get("logo"),
            "color": f"#{color}" if color else None,
        }

    @staticmethod
    def _shootout(competitor: dict[str, Any]) -> int | None:
        raw = competitor.get("shootoutScore")
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def _simplify(self, event: dict[str, Any]) -> dict[str, Any]:
        comp = event["competitions"][0]
        home, away = self._sides(event)
        state = event.get("status", {}).get("type", {}).get("state")
        hm, am = self._team_meta(home), self._team_meta(away)
        # Real advancer + shootout (covers knockout ties decided on penalties).
        winner_team = None
        if state == "post":
            if home.get("winner"):
                winner_team = hm["name"]
            elif away.get("winner"):
                winner_team = am["name"]
        hs, as_ = self._shootout(home), self._shootout(away)
        pens = f"{hs}-{as_}" if hs is not None and as_ is not None else None
        return {
            "match_id": int(event["id"]),
            "status": _STATE_TO_STATUS.get(state, state),
            "kickoff_utc": event.get("date"),
            "stage": (event.get("season", {}) or {}).get("slug"),
            "home_team": hm["name"],
            "away_team": am["name"],
            "home_meta": hm,
            "away_meta": am,
            "home_goals": self._score(home) if state == "post" else None,
            "away_goals": self._score(away) if state == "post" else None,
            "winner_team": winner_team,
            "pens": pens,
            "venue": (comp.get("venue", {}) or {}).get("fullName"),
        }

    # --- public API (matches DataProvider) ---------------------------------------------

    def list_fixtures(self, status: str | None = None) -> list[dict[str, Any]]:
        out = [self._simplify(e) for e in self._events()]
        if status == "NS":
            out = [f for f in out if f["status"] == "NS"]
        elif status == "FT":
            out = [f for f in out if f["status"] == "FT"]
        return out

    def get_result(self, match_id: int) -> tuple[str, str] | None:
        e = self._find_event(match_id)
        if e is None:
            return None
        if e.get("status", {}).get("type", {}).get("state") != "post":
            return None
        home, away = self._sides(e)
        hg, ag = self._score(home), self._score(away)
        outcome = _outcome(hg, ag)
        if outcome is None:
            return None
        return outcome, f"{hg}-{ag}"

    def get_match_context(self, match_id: int) -> MatchContext:
        e = self._find_event(match_id)
        if e is None:
            raise ValueError(f"event {match_id} not found in ESPN window {self.window}")
        home_c, away_c = self._sides(e)
        kickoff = e.get("date")
        comp = e["competitions"][0]
        home = self._team_form(home_c, kickoff)
        away = self._team_form(away_c, kickoff)
        return MatchContext(
            match_id=match_id,
            stage=(e.get("season", {}) or {}).get("slug"),
            kickoff_utc=kickoff,
            home=home,
            away=away,
            head_to_head=self._head_to_head(
                home_c.get("team", {}).get("id"), away_c.get("team", {}).get("id"), kickoff
            ),
            venue=(comp.get("venue", {}) or {}).get("fullName"),
        )

    # --- helpers -----------------------------------------------------------------------

    def _team_form(self, competitor: dict[str, Any], before_date: str | None) -> TeamForm:
        team = competitor.get("team", {})
        team_id = team.get("id")
        form_str = competitor.get("form") or ""
        last5 = [c for c in list(form_str)[-5:] if c in {"W", "D", "L"}]
        gf, ga = self._goal_averages(team_id, before_date)
        color = team.get("color")
        return TeamForm(
            name=team.get("displayName"),
            abbr=team.get("abbreviation"),
            logo=team.get("logo"),
            color=f"#{color}" if color else None,
            last5=last5,
            goals_for_avg=gf,
            goals_against_avg=ga,
            key_absences=[],
        )

    def _team_finished_before(
        self, team_id: str | None, before_date: str | None
    ) -> list[dict[str, Any]]:
        out = []
        for e in self._events():
            if e.get("status", {}).get("type", {}).get("state") != "post":
                continue
            date = e.get("date")
            if before_date and date and date >= before_date:
                continue
            home, away = self._sides(e)
            ids = {home.get("team", {}).get("id"), away.get("team", {}).get("id")}
            if team_id in ids:
                out.append(e)
        out.sort(key=lambda x: x.get("date") or "")
        return out

    def _goal_averages(
        self, team_id: str | None, before_date: str | None
    ) -> tuple[float | None, float | None]:
        scored: list[int] = []
        conceded: list[int] = []
        for e in self._team_finished_before(team_id, before_date):
            home, away = self._sides(e)
            is_home = home.get("team", {}).get("id") == team_id
            hg, ag = self._score(home), self._score(away)
            if hg is None or ag is None:
                continue
            scored.append(hg if is_home else ag)
            conceded.append(ag if is_home else hg)
        gf = round(sum(scored) / len(scored), 2) if scored else None
        ga = round(sum(conceded) / len(conceded), 2) if conceded else None
        return gf, ga

    def _head_to_head(
        self, home_id: str | None, away_id: str | None, before_date: str | None
    ) -> list[str]:
        results: list[str] = []
        for e in self._team_finished_before(home_id, before_date):
            home, away = self._sides(e)
            ids = {home.get("team", {}).get("id"), away.get("team", {}).get("id")}
            if away_id not in ids:
                continue
            hg, ag = self._score(home), self._score(away)
            outcome = _outcome(hg, ag)
            if outcome is None:
                results.append("?")
            elif outcome == "draw":
                results.append("D")
            else:
                home_is_first = home.get("team", {}).get("id") == home_id
                results.append("W" if (outcome == "home") == home_is_first else "L")
        return results
