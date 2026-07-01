"""The knockout bracket: structure, teams, and the live tournament state.

What: The fixed FIFA World Cup 2026 knockout tree (Round of 32 -> Round of 16 ->
Quarter-finals -> Semi-finals -> Final), a small database of the 32 knockout teams
(crest, colour, recent form, strength rating), and a builder that returns the current
state of the bracket - which matches are already decided and which are still to predict.

Why: The whole "re-do" is a forward simulation of this tree. The simulator needs one
honest, self-contained description of where the tournament is right now and how every
match feeds the next. Bundling it makes the demo run fully offline; refreshing from the
live ESPN provider keeps it current on matchday.

How it fits: `simulate.py` reads `build_bracket_state()`, fills in the unknown winners
with the agent, and walks the tree to a champion. The dashboard renders the result.

On camera: "This is the real bracket as it stands today - Brazil are through, the rest is
still open. Now I let the agent play it out."
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# --- The 32 knockout teams ------------------------------------------------------------
# rating is a 0-100 strength prior (FIFA-ranking-informed) that, together with recent
# form, gives the offline simulation a believable pecking order. form is each team's last
# five results (most recent last), straight from ESPN.
TEAMS: dict[str, dict[str, Any]] = {
    "Argentina": {"abbr": "ARG", "color": "#74acdf", "rating": 93, "form": "WWWWW"},
    "France": {"abbr": "FRA", "color": "#000080", "rating": 92, "form": "WWWWL"},
    "Spain": {"abbr": "ESP", "color": "#c60b1e", "rating": 91, "form": "WWDWD"},
    "Brazil": {"abbr": "BRA", "color": "#fee000", "rating": 90, "form": "WWWDW"},
    "England": {"abbr": "ENG", "color": "#ffffff", "rating": 89, "form": "WDWWW"},
    "Portugal": {"abbr": "POR", "color": "#da291c", "rating": 87, "form": "DWDWW"},
    "Netherlands": {"abbr": "NED", "color": "#fb5d00", "rating": 86, "form": "WWDWL"},
    "Germany": {"abbr": "GER", "color": "#cccccc", "rating": 85, "form": "LWWWW"},
    "Belgium": {"abbr": "BEL", "color": "#E30613", "rating": 83, "form": "WDDWW"},
    "Croatia": {"abbr": "CRO", "color": "#ff0000", "rating": 81, "form": "WWLWL"},
    "Morocco": {"abbr": "MAR", "color": "#df2027", "rating": 80, "form": "WWDDW"},
    "Colombia": {"abbr": "COL", "color": "#fbd632", "rating": 79, "form": "DWWWW"},
    "Switzerland": {"abbr": "SUI", "color": "#FF0000", "rating": 78, "form": "WWDDW"},
    "Senegal": {"abbr": "SEN", "color": "#1d8a4c", "rating": 78, "form": "WLLDL"},
    "Japan": {"abbr": "JPN", "color": "#000555", "rating": 77, "form": "LDWDW"},
    "Mexico": {"abbr": "MEX", "color": "#006847", "rating": 77, "form": "WWWWW"},
    "Norway": {"abbr": "NOR", "color": "#C8102E", "rating": 77, "form": "LWWDW"},
    "United States": {"abbr": "USA", "color": "#d42339", "rating": 76, "form": "LWWLW"},
    "Ecuador": {"abbr": "ECU", "color": "#ffdd00", "rating": 75, "form": "WDLWW"},
    "Austria": {"abbr": "AUT", "color": "#d72b2c", "rating": 75, "form": "DLWWW"},
    "Sweden": {"abbr": "SWE", "color": "#fecb00", "rating": 74, "form": "DLWDL"},
    "Ivory Coast": {"abbr": "CIV", "color": "#FF8200", "rating": 74, "form": "WLWWW"},
    "Egypt": {"abbr": "EGY", "color": "#D20300", "rating": 73, "form": "DWDLW"},
    "Algeria": {"abbr": "ALG", "color": "#4F9A44", "rating": 73, "form": "DWLWW"},
    "Australia": {"abbr": "AUS", "color": "#FFCD00", "rating": 73, "form": "DLWDL"},
    "Canada": {"abbr": "CAN", "color": "#ed2224", "rating": 73, "form": "WLWDD"},
    "Paraguay": {"abbr": "PAR", "color": "#ea2300", "rating": 72, "form": "DWLWL"},
    "Bosnia-Herzegovina": {"abbr": "BIH", "color": "#112855", "rating": 72, "form": "WLDDD"},
    "Ghana": {"abbr": "GHA", "color": "#cdac5a", "rating": 71, "form": "LDWDL"},
    "South Africa": {"abbr": "RSA", "color": "#FFB81C", "rating": 70, "form": "LWDLW"},
    "Congo DR": {"abbr": "COD", "color": "#418fde", "rating": 69, "form": "WLDLD"},
    "Cape Verde": {"abbr": "CPV", "color": "#1c3f94", "rating": 66, "form": "DDDWW"},
}

_ESPN_LOGO = "https://a.espncdn.com/i/teamlogos/countries/500/{slug}.png"
# ESPN crest slug where it differs from the lowercased abbreviation.
_LOGO_SLUG = {"COD": "rdc"}


def team_meta(name: str) -> dict[str, Any]:
    """Return display + model metadata for a team (crest, colour, form, rating)."""
    t = TEAMS.get(name)
    if not t:
        return {"name": name, "abbr": name[:3].upper(), "logo": None, "color": None,
                "rating": 70, "form": []}
    slug = _LOGO_SLUG.get(t["abbr"], t["abbr"].lower())
    return {
        "name": name,
        "abbr": t["abbr"],
        "logo": _ESPN_LOGO.format(slug=slug),
        "color": t["color"],
        "rating": t["rating"],
        "form": [c for c in t["form"] if c in "WDL"],
    }


# --- The fixed knockout tree ----------------------------------------------------------
# Match ids: R32 = 1..16, R16 = 17..24, QF = 25..28, SF = 29..30, Final = 31.
# Each R32 seed: (id, home, away). Layout follows the official 2026 draw: ids 1-8 are the
# LEFT half (top -> bottom), ids 9-16 the RIGHT half. Adjacent odd/even pairs meet in the
# Round of 16.
_SEED_R32: list[tuple[int, str, str]] = [
    # Left half
    (1, "Germany", "Paraguay"),
    (2, "Sweden", "France"),
    (3, "South Africa", "Canada"),
    (4, "Netherlands", "Morocco"),
    (5, "Portugal", "Croatia"),
    (6, "Spain", "Austria"),
    (7, "United States", "Bosnia-Herzegovina"),
    (8, "Belgium", "Senegal"),
    # Right half
    (9, "Brazil", "Japan"),
    (10, "Norway", "Ivory Coast"),
    (11, "Mexico", "Ecuador"),
    (12, "England", "Congo DR"),
    (13, "Argentina", "Cape Verde"),
    (14, "Australia", "Egypt"),
    (15, "Switzerland", "Algeria"),
    (16, "Colombia", "Ghana"),
]

# Finished Round-of-32 results, live from ESPN as of 2026-07-01. `winner` overrides the
# goals-based winner so penalty shootouts resolve correctly; `pens` is the shootout score
# in home-away orientation (rendered as "1-1 (3-4 pens)").
_R32_RESULTS: dict[int, dict[str, Any]] = {
    1: {"home_goals": 1, "away_goals": 1, "winner": "Paraguay", "pens": "3-4"},   # Paraguay win 4-3 on pens; Germany out
    2: {"home_goals": 0, "away_goals": 3, "winner": "France"},                    # France 3-0 Sweden
    3: {"home_goals": 0, "away_goals": 1, "winner": "Canada"},
    4: {"home_goals": 1, "away_goals": 1, "winner": "Morocco", "pens": "2-3"},    # Morocco win 3-2 on pens; Netherlands out
    9: {"home_goals": 2, "away_goals": 1, "winner": "Brazil"},
    10: {"home_goals": 2, "away_goals": 1, "winner": "Norway"},                   # Norway 2-1 Ivory Coast
    11: {"home_goals": 2, "away_goals": 0, "winner": "Mexico"},                   # Mexico 2-0 Ecuador
}

# winner of source match -> (target match id, "home" | "away" slot)
_LINKS: dict[int, tuple[int, str]] = {
    # Round of 16 (adjacent R32 pairs)
    1: (17, "home"), 2: (17, "away"),
    3: (18, "home"), 4: (18, "away"),
    5: (19, "home"), 6: (19, "away"),
    7: (20, "home"), 8: (20, "away"),
    9: (21, "home"), 10: (21, "away"),
    11: (22, "home"), 12: (22, "away"),
    13: (23, "home"), 14: (23, "away"),
    15: (24, "home"), 16: (24, "away"),
    # Quarter-finals
    17: (25, "home"), 18: (25, "away"),
    19: (26, "home"), 20: (26, "away"),
    21: (27, "home"), 22: (27, "away"),
    23: (28, "home"), 24: (28, "away"),
    # Semi-finals (left: 29, right: 30)
    25: (29, "home"), 26: (29, "away"),
    27: (30, "home"), 28: (30, "away"),
    # Final
    29: (31, "home"), 30: (31, "away"),
}

ROUNDS: list[tuple[str, str]] = [
    ("R32", "Round of 32"),
    ("R16", "Round of 16"),
    ("QF", "Quarter-finals"),
    ("SF", "Semi-finals"),
    ("F", "Final"),
]

_ROUND_OF: dict[int, str] = {
    **{i: "R32" for i in range(1, 17)},
    **{i: "R16" for i in range(17, 25)},
    **{i: "QF" for i in range(25, 29)},
    **{i: "SF" for i in range(29, 31)},
    31: "F",
}

# Stadiums for the Round of 32 (real ESPN venues) for on-screen flavour. Later rounds are
# neutral and undecided until the bracket plays out, so they are left unset.
_VENUES: dict[int, str] = {
    1: "Gillette Stadium", 2: "MetLife Stadium", 3: "SoFi Stadium", 4: "Estadio BBVA",
    5: "BMO Field", 6: "SoFi Stadium", 7: "Levi's Stadium", 8: "Lumen Field",
    9: "NRG Stadium", 10: "AT&T Stadium", 11: "Estadio Banorte", 12: "Mercedes-Benz Stadium",
    13: "Hard Rock Stadium", 14: "AT&T Stadium", 15: "BC Place",
    16: "GEHA Field at Arrowhead", 31: "MetLife Stadium",
}


def round_name(code: str) -> str:
    return dict(ROUNDS).get(code, code)


def _winner_of(home: str | None, away: str | None, hg: int | None, ag: int | None) -> str | None:
    if home is None or away is None or hg is None or ag is None:
        return None
    return home if hg >= ag else away


def _flip_pens(pens: str | None) -> str | None:
    """Reverse a 'home-away' shootout score so it matches our orientation."""
    if not pens or "-" not in pens:
        return pens
    a, b = pens.split("-", 1)
    return f"{b}-{a}"


def build_bracket_state(provider: Any | None = None) -> dict[str, Any]:
    """Return the current knockout bracket: every match, its teams, and known results.

    The bundled seed already reflects the live tournament. When a `provider` is given we
    best-effort refresh Round-of-32 results from it (matching by team name), so a live
    `oracle export` stays current without re-coding the bracket.
    """
    matches: dict[int, dict[str, Any]] = {}
    for mid in range(1, 32):
        matches[mid] = {
            "id": mid,
            "round": _ROUND_OF[mid],
            "round_name": round_name(_ROUND_OF[mid]),
            "venue": _VENUES.get(mid),
            "home": None,
            "away": None,
            "home_goals": None,
            "away_goals": None,
            "pens": None,
            "status": "NS",
            "winner": None,
            "feeds": _LINKS.get(mid),
        }

    for mid, home, away in _SEED_R32:
        m = matches[mid]
        m.update(home=home, away=away)
        res = _R32_RESULTS.get(mid)
        if res:
            hg, ag = res["home_goals"], res["away_goals"]
            m.update(
                status="FT",
                home_goals=hg,
                away_goals=ag,
                pens=res.get("pens"),
                winner=res.get("winner") or _winner_of(home, away, hg, ag),
            )

    if provider is not None:
        _refresh_from_provider(matches, provider)

    # Propagate any decided Round-of-32 winners into their Round-of-16 slot.
    for mid in range(1, 17):
        _advance_known_winner(matches, mid)

    return {"matches": matches, "rounds": ROUNDS}


def _refresh_from_provider(matches: dict[int, dict[str, Any]], provider: Any) -> None:
    """Overlay live finished R32 results onto the seed, matched by team name."""
    try:
        fixtures = provider.list_fixtures(status="FT")
    except Exception:  # noqa: BLE001 - live data is best-effort; seed is the fallback
        return
    by_pair: dict[frozenset[str], dict[str, Any]] = {}
    for f in fixtures:
        ht, at = f.get("home_team"), f.get("away_team")
        if ht and at:
            by_pair[frozenset({ht, at})] = f
    for mid in range(1, 17):
        m = matches[mid]
        f = by_pair.get(frozenset({m["home"], m["away"]}))
        if not f or f.get("home_goals") is None:
            continue
        # Align goals (and any shootout) to our home/away orientation.
        if f["home_team"] == m["home"]:
            hg, ag, pens = f["home_goals"], f["away_goals"], f.get("pens")
        else:
            hg, ag = f["away_goals"], f["home_goals"]
            pens = _flip_pens(f.get("pens"))
        # Honour the real advancer (covers extra time / penalties); fall back to goals.
        winner = f.get("winner_team") or _winner_of(m["home"], m["away"], hg, ag)
        m.update(status="FT", home_goals=hg, away_goals=ag, pens=pens, winner=winner)


def _advance_known_winner(matches: dict[int, dict[str, Any]], mid: int) -> None:
    m = matches[mid]
    if not m["winner"] or not m["feeds"]:
        return
    target_id, slot = m["feeds"]
    matches[target_id][slot] = m["winner"]


def initial_teams_in_round(state: dict[str, Any], code: str) -> list[str]:
    """Names of teams already locked into a given round (known winners)."""
    out: list[str] = []
    for m in state["matches"].values():
        if m["round"] != code:
            continue
        for side in ("home", "away"):
            if m[side]:
                out.append(m[side])
    return out


__all__ = [
    "TEAMS",
    "ROUNDS",
    "team_meta",
    "round_name",
    "build_bracket_state",
]
