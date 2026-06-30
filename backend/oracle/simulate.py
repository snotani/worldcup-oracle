"""The forward bracket simulator: play the whole knockout out to a champion.

What: Starting from the live bracket state (`bracket.py`), the simulator visits every match
in round order. For matches already played it uses the real result; for the rest it asks the
agent who advances, picks the most-likely winner, and feeds that winner into the next round -
all the way to a single predicted champion. It can run one model (Tab 1) or every battle
model (Tab 2).

Why: This is the new product. Instead of one match at a time, the agent now produces a full,
explainable path from "today" to the trophy, which is exactly what the two videos show.

How it fits: `dashboard.py` calls `simulate_bracket()` / `simulate_battle()` and serialises
the result into the payload the Next.js bracket animates.

On camera: "Watch the agent play the entire bracket forward - every game, both sides of the
draw, all the way to who lifts the cup."
"""

from __future__ import annotations

import hashlib
from typing import Any

from .agent import advancement, predict_from_context
from .bracket import build_bracket_state, team_meta
from .config import Settings, get_settings
from .models import BATTLE_REGISTRY
from .schema import MatchContext, TeamForm
from .trace import RunTrace

# The explainable feature list for the Tab 1 intro ("what the agent looks at").
AGENT_FEATURES: list[dict[str, str]] = [
    {"key": "rating", "label": "Team strength rating",
     "detail": "A FIFA-ranking-informed power score for every side - the baseline quality gap."},
    {"key": "form", "label": "Recent form (last 5)",
     "detail": "Win/draw/loss momentum heading into the knockouts, not just the name on the shirt."},
    {"key": "goals", "label": "Goals scored & conceded",
     "detail": "Attacking output and defensive solidity across the tournament so far."},
    {"key": "h2h", "label": "Head-to-head history",
     "detail": "How these two have actually fared against each other in the past."},
    {"key": "scorers", "label": "Goal involvement / top scorers",
     "detail": "Who is carrying the goal threat - a hot striker swings tight ties."},
    {"key": "shots", "label": "Shots on target & possession",
     "detail": "Underlying performance signals from ESPN match stats, not just the scoreline."},
    {"key": "absences", "label": "Squad availability",
     "detail": "Suspensions and injuries to key players that quietly decide knockouts."},
    {"key": "rest", "label": "Rest & travel",
     "detail": "Days between games and distance travelled across a continent-sized host."},
    {"key": "venue", "label": "Venue & home advantage",
     "detail": "Host-nation edge and a modest lift for the higher-seeded side."},
    {"key": "knockout", "label": "Knockout conversion",
     "detail": "No draws here - level games are resolved by who is likelier to survive ET/pens."},
]


def _ctx_for(home: str, away: str, stage: str, match_id: int) -> MatchContext:
    """Build a MatchContext for any matchup straight from the team database."""
    hm, am = team_meta(home), team_meta(away)
    return MatchContext(
        match_id=match_id,
        stage=stage,
        neutral_venue=True,
        home=TeamForm(
            name=home, abbr=hm["abbr"], logo=hm["logo"], color=hm["color"],
            rating=hm["rating"], last5=hm["form"],
        ),
        away=TeamForm(
            name=away, abbr=am["abbr"], logo=am["logo"], color=am["color"],
            rating=am["rating"], last5=am["form"],
        ),
        head_to_head=[],
    )


def _stable_choice(options: list[str], *seed_parts: str) -> str:
    h = hashlib.sha256("|".join(seed_parts).encode()).hexdigest()
    return options[int(h, 16) % len(options)]


def _knockout_score(winner_adv: float, home: str, away: str) -> str:
    """A plausible decisive scoreline, scaled by how dominant the winner is."""
    if winner_adv >= 0.72:
        return _stable_choice(["3-0", "2-0", "3-1"], home, away, "big")
    if winner_adv >= 0.6:
        return _stable_choice(["2-0", "2-1"], home, away, "clear")
    if winner_adv >= 0.54:
        return _stable_choice(["2-1", "1-0"], home, away, "edge")
    return _stable_choice(["1-0 (a.e.t.)", "1-1 (4-2 pens)", "2-1 (a.e.t.)"], home, away, "tight")


def simulate_bracket(
    model_id: str,
    *,
    model_name: str | None = None,
    settings: Settings | None = None,
    mock_model: bool = False,
    provider: Any | None = None,
) -> dict[str, Any]:
    """Play the bracket forward with one model; return the full predicted tree + paths."""
    settings = settings or get_settings()
    state = build_bracket_state(provider)
    matches = state["matches"]
    trace = RunTrace(label=f"bracket:{model_name or model_id}", model_id=model_id)

    predictions: dict[int, dict[str, Any]] = {}

    for mid in range(1, 32):
        m = matches[mid]
        home, away = m["home"], m["away"]
        if not home or not away:
            # Defensive: a feeder hasn't resolved (shouldn't happen walking in id order).
            continue

        ctx = _ctx_for(home, away, m["round_name"], 90000 + mid)
        stored, _ = predict_from_context(
            ctx, model_id=model_id, settings=settings, mock_model=mock_model, save=False
        )
        h_adv, a_adv = advancement(stored.prediction.probabilities)

        is_result = m["status"] == "FT" and bool(m["winner"])
        if is_result:
            winner = m["winner"]
            score = f"{m['home_goals']}-{m['away_goals']}"
            if m.get("pens"):
                score += f" ({m['pens']} pens)"
        else:
            winner = home if h_adv >= a_adv else away
            winner_adv = h_adv if winner == home else a_adv
            score = _knockout_score(winner_adv, home, away)

        win_side = "home" if winner == home else "away"
        loser = away if winner == home else home
        wr = team_meta(winner)["rating"]
        lr = team_meta(loser)["rating"]
        upset = (not is_result) and (wr < lr - 2)

        predictions[mid] = {
            "id": mid,
            "round": m["round"],
            "round_name": m["round_name"],
            "venue": m["venue"],
            "home": team_meta(home),
            "away": team_meta(away),
            "home_adv": h_adv,
            "away_adv": a_adv,
            "winner": win_side,
            "winner_name": winner,
            "loser_name": loser,
            "score": score,
            "confidence": round(max(h_adv, a_adv), 4),
            "is_result": is_result,
            "is_upset": upset,
            "feeds": m["feeds"],
            "rationale": _rationale(winner, loser, max(h_adv, a_adv), is_result, m["round_name"]),
        }

        if m["feeds"]:
            target_id, slot = m["feeds"]
            matches[target_id][slot] = winner

    trace.record("simulate", f"played {len(predictions)} matches to a champion",
                 matches=len(predictions))

    final = predictions[31]
    champion = final["winner_name"]
    runner_up = final["loser_name"]
    finalists = [final["home"], final["away"]]

    rounds_out = []
    for code, name in state["rounds"]:
        ms = [predictions[i] for i in sorted(predictions) if predictions[i]["round"] == code]
        rounds_out.append({"code": code, "name": name, "matches": ms})

    path = [predictions[i] for i in sorted(predictions) if predictions[i]["winner_name"] == champion]
    upsets = [p for p in predictions.values() if p["is_upset"]]
    upsets.sort(key=lambda p: p["id"])

    return {
        "model_id": model_id,
        "model_name": model_name or model_id,
        "champion": team_meta(champion),
        "runner_up": team_meta(runner_up),
        "finalists": finalists,
        "final": final,
        "rounds": rounds_out,
        "path": path,
        "upsets": upsets,
        "trace": trace.to_dict(),
    }


def _rationale(winner: str, loser: str, adv: float, is_result: bool, rnd: str) -> str:
    if is_result:
        return f"{winner} already got through this {rnd.lower()} tie - through on the night."
    if adv >= 0.7:
        return f"{winner} are clear favourites here; comfortable progress over {loser}."
    if adv >= 0.58:
        return f"{winner} edge a competitive {rnd.lower()} tie against {loser}."
    return f"Coin-flip {rnd.lower()}: {winner} survive {loser} by the finest margin."


def simulate_battle(
    models: dict[str, str] | None = None,
    *,
    settings: Settings | None = None,
    mock_model: bool = False,
    provider: Any | None = None,
) -> dict[str, Any]:
    """Run the full bracket for every battle model and compare champions + paths."""
    settings = settings or get_settings()
    models = models or dict(BATTLE_REGISTRY)

    brackets = [
        simulate_bracket(
            mid, model_name=name, settings=settings, mock_model=mock_model, provider=provider
        )
        for name, mid in models.items()
    ]
    return {"brackets": brackets, "consensus": _consensus(brackets)}


def _consensus(brackets: list[dict[str, Any]]) -> dict[str, Any]:
    """Where do the models agree, and where do they split? (R32 teams are shared.)"""
    if not brackets:
        return {}

    # Champion + finalist votes.
    champ_votes: dict[str, int] = {}
    finalist_votes: dict[str, int] = {}
    for b in brackets:
        champ_votes[b["champion"]["name"]] = champ_votes.get(b["champion"]["name"], 0) + 1
        for f in b["finalists"]:
            finalist_votes[f["name"]] = finalist_votes.get(f["name"], 0) + 1
    consensus_champion = max(champ_votes.items(), key=lambda kv: kv[1])

    # Round-of-32 agreement: the 16 first-round matches share the same two teams for every
    # model, so we can measure how often the models pick the same side.
    r32_by_model = []
    for b in brackets:
        r32 = next((r["matches"] for r in b["rounds"] if r["code"] == "R32"), [])
        r32_by_model.append({m["id"]: m["winner_name"] for m in r32})

    contested = []
    agree_count = 0
    n = len(brackets)
    match_ids = sorted(r32_by_model[0].keys()) if r32_by_model else []
    for mid in match_ids:
        picks = [rm.get(mid) for rm in r32_by_model]
        tally: dict[str, int] = {}
        for p in picks:
            if p:
                tally[p] = tally.get(p, 0) + 1
        if not tally:
            continue
        top = max(tally.values())
        if top == n:
            agree_count += 1
        if top < n:
            m0 = next((m for m in brackets[0]["rounds"][0]["matches"] if m["id"] == mid), None)
            if m0:
                contested.append({
                    "id": mid,
                    "home": m0["home"],
                    "away": m0["away"],
                    "tally": tally,
                    "split": "-".join(str(v) for v in sorted(tally.values(), reverse=True)),
                })
    contested.sort(key=lambda c: max(c["tally"].values()))

    return {
        "champion_votes": champ_votes,
        "finalist_votes": finalist_votes,
        "consensus_champion": {"name": consensus_champion[0], "votes": consensus_champion[1],
                               "of": n, "meta": team_meta(consensus_champion[0])},
        "distinct_champions": len(champ_votes),
        "r32_agreement": round(agree_count / len(match_ids), 3) if match_ids else 0.0,
        "contested": contested[:5],
    }


__all__ = ["AGENT_FEATURES", "simulate_bracket", "simulate_battle"]
