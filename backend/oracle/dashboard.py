"""Builds the data payload the dashboard renders.

What: Assembles one JSON document with everything the three content angles need: the accuracy
scoreboard (A), the model-battle leaderboard + per-match picks (B), and persona cards (C).
Why: One builder shared by the CLI `export` command (static JSON for a self-contained, easily
recorded dashboard) and the FastAPI server (live).
How it fits: `cli.py export` writes this to `frontend/public/data/dashboard.json`; `api.py`
returns it from an endpoint.
On camera: "Everything you see on the dashboard comes from this one payload the agent produced."

Live model calls are the expensive part, so they are limited (finished/upcoming caps) and run
concurrently across a thread pool.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from .agent import predict_match
from .config import Settings, get_settings
from .eval.baselines import all_baselines
from .eval.metrics import EvalSample, summarize
from .models import BATTLE_REGISTRY
from .personas import PERSONAS, get_persona
from .schema import MatchContext, StoredPrediction
from .tools import get_provider
from .trace import RunTrace


def _resolve_models(friendly: list[str]) -> dict[str, str]:
    """Map friendly battle names to model ids (unknown names pass through as raw ids)."""
    return {name: BATTLE_REGISTRY.get(name, name) for name in friendly}


def _probs_dict(sp: StoredPrediction) -> dict[str, float]:
    p = sp.prediction.probabilities
    return {"home": p.home, "draw": p.draw, "away": p.away}


def _team_block(fixture: dict, side: str) -> dict:
    """Extract a team's display block (name/abbr/logo/color) from a simplified fixture."""
    meta = fixture.get(f"{side}_meta") or {}
    return {
        "name": meta.get("name") or fixture.get(f"{side}_team"),
        "abbr": meta.get("abbr"),
        "logo": meta.get("logo"),
        "color": meta.get("color"),
    }


def _outcome_label(pick: str, home: str, away: str) -> str:
    return home if pick == "home" else away if pick == "away" else "Draw"


def _battle_match(u: dict, picks: list[dict]) -> dict:
    """Assemble one upcoming-match card, including how much the models disagree.

    Even when every model picks the same winner, they rarely agree on *how* sure they are or
    on the scoreline. We quantify that so the UI can lead with the real debates instead of the
    blowouts everyone calls the same way.
    """
    n = len(picks) or 1
    votes = {"home": 0, "draw": 0, "away": 0}
    for p in picks:
        votes[p["pick"]] += 1
    consensus = max(votes.items(), key=lambda kv: kv[1])
    distinct_picks = sum(1 for v in votes.values() if v)

    # Crowd = mean distribution; each model's L1 distance from it = how contrarian it is.
    mean = {k: sum(p["probs"][k] for p in picks) / n for k in ("home", "draw", "away")}
    for p in picks:
        p["delta_vs_crowd"] = round(
            sum(abs(p["probs"][k] - mean[k]) for k in ("home", "draw", "away")) / 2, 3
        )
        p["against_consensus"] = p["pick"] != consensus[0]
    maverick = max(picks, key=lambda p: p["delta_vs_crowd"])
    for p in picks:
        p["is_maverick"] = p is maverick

    lead = consensus[0]
    prob_spread = max(p["probs"][lead] for p in picks) - min(p["probs"][lead] for p in picks)
    scorelines = {p["predicted_score"] for p in picks if p["predicted_score"]}
    # 0-1 debate meter: how split the votes are + how wide the probability spread is.
    disagreement = round(
        0.6 * ((distinct_picks - 1) / 2) + 0.3 * min(prob_spread / 0.5, 1.0)
        + 0.1 * min((len(scorelines) - 1) / 3, 1.0),
        3,
    )
    if distinct_picks == 1:
        split_label = "Unanimous"
    else:
        counts = [str(v) for _, v in sorted(votes.items(), key=lambda kv: -kv[1]) if v]
        split_label = "–".join(counts) + " split"

    return {
        "match_id": u["match_id"],
        "home_team": u["home_team"],
        "away_team": u["away_team"],
        "home": _team_block(u, "home"),
        "away": _team_block(u, "away"),
        "kickoff_utc": u["kickoff_utc"],
        "stage": u["stage"],
        "venue": u.get("venue"),
        "consensus": {"pick": consensus[0], "votes": consensus[1], "of": n},
        "vote_split": votes,
        "distinct_picks": distinct_picks,
        "split_label": split_label,
        "prob_spread": round(prob_spread, 3),
        "score_spread": len(scorelines),
        "disagreement": disagreement,
        "maverick": {
            "name": maverick["name"],
            "model_id": maverick["model_id"],
            "pick": maverick["pick"],
            "delta": maverick["delta_vs_crowd"],
        },
        "picks": picks,
    }


def _battle_insights(matches: list[dict]) -> dict:
    """Cross-match 'hot takes' for the top of the battle tab."""
    if not matches:
        return {}

    def teams(m: dict) -> str:
        return f"{m['home_team']} v {m['away_team']}"

    # Biggest debate: most genuinely split fixture.
    debate = max(matches, key=lambda m: (m["disagreement"], m["prob_spread"]))
    biggest_debate = {
        "match_id": debate["match_id"],
        "label": teams(debate),
        "home": debate["home"],
        "away": debate["away"],
        "split_label": debate["split_label"],
        "disagreement": debate["disagreement"],
    }

    # Boldest call: single most confident pick anywhere.
    all_picks = [(m, p) for m in matches for p in m["picks"]]
    bm, bp = max(all_picks, key=lambda mp: mp[1]["confidence"])
    boldest_call = {
        "match_id": bm["match_id"],
        "label": teams(bm),
        "model": bp["name"],
        "model_id": bp["model_id"],
        "pick": bp["pick"],
        "pick_label": _outcome_label(bp["pick"], bm["home_team"], bm["away_team"]),
        "confidence": bp["confidence"],
    }

    # Upset alert: most confident pick that goes against the room (or backs the away side).
    contrarian = [(m, p) for m, p in all_picks if p["against_consensus"]]
    pool = contrarian or [(m, p) for m, p in all_picks if p["pick"] == "away"]
    upset_alert = None
    if pool:
        um, up = max(pool, key=lambda mp: mp[1]["confidence"])
        upset_alert = {
            "match_id": um["match_id"],
            "label": teams(um),
            "model": up["name"],
            "model_id": up["model_id"],
            "pick": up["pick"],
            "pick_label": _outcome_label(up["pick"], um["home_team"], um["away_team"]),
            "confidence": up["confidence"],
            "against_consensus": up["against_consensus"],
        }

    # Maverick model: who disagrees with the crowd most often / most strongly.
    by_model: dict[str, dict] = {}
    for m in matches:
        for p in m["picks"]:
            agg = by_model.setdefault(
                p["name"],
                {"name": p["name"], "model_id": p["model_id"], "contrarian": 0, "delta": 0.0},
            )
            agg["contrarian"] += int(p["against_consensus"])
            agg["delta"] += p["delta_vs_crowd"]
    maverick_model = max(
        by_model.values(), key=lambda a: (a["contrarian"], a["delta"]), default=None
    )
    if maverick_model:
        maverick_model = {
            **maverick_model,
            "delta": round(maverick_model["delta"] / max(len(matches), 1), 3),
        }

    return {
        "biggest_debate": biggest_debate,
        "boldest_call": boldest_call,
        "upset_alert": upset_alert,
        "maverick_model": maverick_model,
    }


def build_payload(
    *,
    settings: Settings | None = None,
    mock_model: bool = False,
    battle: list[str] | None = None,
    persona: str = "gaffer",
    upcoming_limit: int = 6,
    finished_limit: int = 8,
    workers: int = 6,
) -> dict:
    settings = settings or get_settings()
    provider = get_provider(settings)
    battle = battle or list(BATTLE_REGISTRY.keys())
    models = _resolve_models(battle)
    default_id = settings.default_model

    # Warm the data cache once so concurrent workers read from disk, not the network.
    finished = provider.list_fixtures(status="FT")[-finished_limit:]
    upcoming = provider.list_fixtures(status="NS")[:upcoming_limit]

    finished_ids = [f["match_id"] for f in finished]
    upcoming_ids = [u["match_id"] for u in upcoming]

    # Model ids needed: every battle model, plus the default (for the scoreboard).
    eval_model_ids = list(dict.fromkeys([*models.values(), default_id]))

    # Build the full job list and run model calls concurrently.
    jobs: list[tuple[int, str]] = []
    for mid in finished_ids:
        for model_id in eval_model_ids:
            jobs.append((mid, model_id))
    for mid in upcoming_ids:
        for model_id in models.values():
            jobs.append((mid, model_id))

    def _run(job: tuple[int, str]) -> tuple[tuple[int, str], StoredPrediction, RunTrace]:
        mid, model_id = job
        stored, trace = predict_match(
            mid, model_id=model_id, settings=settings, mock_model=mock_model, save=False
        )
        return job, stored, trace

    preds: dict[tuple[int, str], tuple[StoredPrediction, RunTrace]] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for job, stored, trace in pool.map(_run, jobs):
            preds[job] = (stored, trace)

    # Contexts + results (cached data; cheap, no model calls).
    contexts: dict[int, MatchContext] = {}
    for mid in set(finished_ids) | set(upcoming_ids):
        contexts[mid] = provider.get_match_context(mid)
    results = {mid: provider.get_result(mid) for mid in finished_ids}

    # --- Angle A: scoreboard (default model vs baselines over finished matches) ---------
    agent_samples: list[EvalSample] = []
    baseline_samples: dict[str, list[EvalSample]] = {}
    rows = []
    fx_by_id = {f["match_id"]: f for f in finished}
    for mid in finished_ids:
        res = results.get(mid)
        if not res:
            continue
        actual_outcome, actual_score = res
        stored = preds[(mid, default_id)][0]
        agent_samples.append(
            EvalSample(_probs_dict(stored), stored.prediction.predicted_outcome, actual_outcome)
        )
        for name, probs in all_baselines(contexts[mid]).items():
            predicted = max(probs.items(), key=lambda kv: kv[1])[0]
            baseline_samples.setdefault(name, []).append(
                EvalSample(probs, predicted, actual_outcome)
            )
        rows.append(
            {
                "match_id": mid,
                "home_team": fx_by_id[mid]["home_team"],
                "away_team": fx_by_id[mid]["away_team"],
                "home": _team_block(fx_by_id[mid], "home"),
                "away": _team_block(fx_by_id[mid], "away"),
                "kickoff_utc": fx_by_id[mid].get("kickoff_utc"),
                "stage": fx_by_id[mid].get("stage"),
                "venue": fx_by_id[mid].get("venue"),
                "actual_outcome": actual_outcome,
                "actual_score": actual_score,
                "agent_pick": stored.prediction.predicted_outcome,
                "agent_correct": stored.prediction.predicted_outcome == actual_outcome,
                "agent_probs": _probs_dict(stored),
                "agent_confidence": stored.prediction.confidence,
            }
        )
    summaries = [summarize(f"agent:{default_id}", agent_samples).to_dict()]
    for name, samples in baseline_samples.items():
        summaries.append(summarize(name, samples).to_dict())
    scoreboard = {
        "model_id": default_id,
        "n_matches": len(rows),
        "summaries": summaries,
        "rows": rows,
    }

    # --- Angle B: leaderboard (each model over finished matches) ------------------------
    standings = []
    for name, model_id in models.items():
        samples = []
        correct = 0
        for mid in finished_ids:
            res = results.get(mid)
            if not res:
                continue
            actual_outcome, _ = res
            stored = preds[(mid, model_id)][0]
            samples.append(
                EvalSample(_probs_dict(stored), stored.prediction.predicted_outcome, actual_outcome)
            )
            if stored.prediction.predicted_outcome == actual_outcome:
                correct += 1
        s = summarize(name, samples)
        standings.append(
            {
                "name": name,
                "model_id": model_id,
                "matches": s.n,
                "correct": correct,
                "accuracy": s.accuracy,
                "brier": s.brier,
                "log_loss": s.log_loss,
            }
        )
    standings.sort(key=lambda s: (-s["accuracy"], s["brier"]))

    # --- Angle B: each model's pick for upcoming fixtures -------------------------------
    battle_matches = []
    for u in upcoming:
        mid = u["match_id"]
        picks = []
        for name, model_id in models.items():
            stored, trace = preds[(mid, model_id)]
            picks.append(
                {
                    "name": name,
                    "model_id": model_id,
                    "pick": stored.prediction.predicted_outcome,
                    "probs": _probs_dict(stored),
                    "predicted_score": stored.prediction.predicted_score,
                    "confidence": stored.prediction.confidence,
                    "rationale": stored.prediction.rationale,
                    "trace": trace.to_dict(),
                }
            )
        battle_matches.append(_battle_match(u, picks))

    # Lead with the debates: spiciest (most disagreement) fixtures first.
    battle_matches.sort(key=lambda m: (-m["disagreement"], m["kickoff_utc"] or ""))
    battle_insights = _battle_insights(battle_matches)

    # --- Angle C: persona cards (reuse default-model upcoming predictions, no extra calls) -
    # Rotate through every persona so the showcase highlights all three voices, but keep the
    # requested persona first so it leads the feed.
    persona_cycle = [persona] + [pid for pid in PERSONAS if pid != persona]
    cards = []
    for idx, u in enumerate(upcoming):
        persona_id = persona_cycle[idx % len(persona_cycle)]
        persona_obj = get_persona(persona_id)
        mid = u["match_id"]
        # Prefer the default model's prediction; fall back to the first battle model.
        if (mid, default_id) in preds:
            key = (mid, default_id)
        else:
            key = (mid, next(iter(models.values())))
        stored, trace = preds[key]
        message = persona_obj.render(stored.prediction, contexts[mid])
        cards.append(
            {
                "match_id": mid,
                "home_team": u["home_team"],
                "away_team": u["away_team"],
                "home": _team_block(u, "home"),
                "away": _team_block(u, "away"),
                "kickoff_utc": u["kickoff_utc"],
                "stage": u["stage"],
                "venue": u.get("venue"),
                "persona": persona_id,
                "persona_name": persona_obj.name,
                "persona_message": message,
                "pick": stored.prediction.predicted_outcome,
                "probs": _probs_dict(stored),
                "predicted_score": stored.prediction.predicted_score,
                "confidence": stored.prediction.confidence,
                "rationale": stored.prediction.rationale,
                "model_id": stored.model_id,
                "trace": trace.to_dict(),
            }
        )

    agent_summary = summaries[0] if summaries else None
    coin = next((s for s in summaries if s["name"] == "coin_flip"), None)
    best_model = standings[0] if standings else None
    summary = {
        "headline_accuracy": agent_summary["accuracy"] if agent_summary else 0.0,
        "headline_brier": agent_summary["brier"] if agent_summary else 0.0,
        "coin_flip_accuracy": coin["accuracy"] if coin else 0.0,
        "edge_vs_coin": (
            (agent_summary["accuracy"] - coin["accuracy"]) if (agent_summary and coin) else 0.0
        ),
        "n_scored": len(rows),
        "n_upcoming": len(battle_matches),
        "n_models": len(standings),
        "total_predictions": len(jobs),
        "best_model": best_model,
        "default_model": default_id,
    }

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "mock": mock_model or settings.use_mock_data,
        "competition": "FIFA World Cup 2026",
        "summary": summary,
        "scoreboard": scoreboard,
        "leaderboard": standings,
        "battle_insights": battle_insights,
        "battle_matches": battle_matches,
        "cards": cards,
        "personas": [
            {"id": p.id, "name": p.name, "tagline": p.tagline} for p in PERSONAS.values()
        ],
    }
