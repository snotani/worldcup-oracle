"""Personas: turn a dry prediction into shareable banter.

What: A small registry of character voices, each able to render a prediction as a punchy,
on-brand message ("trash talk").
Why: Angle C of the content. The numbers are the same; the personality is what makes a clip
shareable. Keeping personas separate proves the point that voice is a thin layer over a solid
agent.
How it fits: `agent.py` optionally applies a persona to produce `persona_message`; the
dashboard renders these as cards.
On camera: "Same prediction, but now the agent has a mouth. This is the exact same model
output - I just wrapped it in a character."
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..schema import MatchContext, MatchPrediction


@dataclass
class Persona:
    """A character voice for prediction output."""

    id: str
    name: str
    tagline: str
    # Optional instruction block you can append to the model prompt for model-written banter.
    prompt_addon: str
    render: Callable[[MatchPrediction, MatchContext], str]


def _pick_names(pred: MatchPrediction, ctx: MatchContext) -> tuple[str, str, str]:
    home, away = ctx.home.name, ctx.away.name
    if pred.predicted_outcome == "home":
        return home, away, home
    if pred.predicted_outcome == "away":
        return home, away, away
    return home, away, "nobody"


def _gaffer(pred: MatchPrediction, ctx: MatchContext) -> str:
    home, away, winner = _pick_names(pred, ctx)
    conf = int(pred.confidence * 100)
    if winner == "nobody":
        return (
            f"{home} vs {away}? Stalemate, lads. {pred.predicted_score or '1-1'} and they "
            f"both go home moaning. I'd stake me reputation on it - {conf}% sure."
        )
    loser = away if winner == home else home
    return (
        f"Right, listen. {winner} are winning this {pred.predicted_score or '2-1'}. "
        f"{loser} haven't got a prayer. {conf}% confident, and I'm never wrong... mostly."
    )


def _professor(pred: MatchPrediction, ctx: MatchContext) -> str:
    p = pred.probabilities
    home, away, winner = _pick_names(pred, ctx)
    return (
        f"The model favours {winner} (home {p.home:.0%} / draw {p.draw:.0%} / away {p.away:.0%}). "
        f"Most likely scoreline {pred.predicted_score or 'n/a'}. Confidence {pred.confidence:.0%}. "
        f"Form and head-to-head drive the edge."
    )


def _hypeman(pred: MatchPrediction, ctx: MatchContext) -> str:
    home, away, winner = _pick_names(pred, ctx)
    if winner == "nobody":
        return f"OH IT'S GONNA BE CHAOS!! {home} vs {away} ends ALL SQUARE, screenshot this!!"
    return (
        f"LOCK IT IN!!! {winner.upper()} ARE TAKING OVER {pred.predicted_score or '2-1'}!! "
        f"You heard it here first - {int(pred.confidence * 100)}% CERTIFIED!!"
    )


_GAFFER_ADDON = (
    "Also write a short, cocky English-football-manager one-liner about your pick. Keep it under "
    "240 characters. Put it in a field called persona_message."
)

PERSONAS: dict[str, Persona] = {
    "gaffer": Persona(
        id="gaffer",
        name="The Gaffer",
        tagline="A cocky touchline manager who's never in doubt.",
        prompt_addon=_GAFFER_ADDON,
        render=_gaffer,
    ),
    "professor": Persona(
        id="professor",
        name="The Professor",
        tagline="Calm, numbers-first analyst.",
        prompt_addon="Add a one-sentence analytical summary in a field called persona_message.",
        render=_professor,
    ),
    "hypeman": Persona(
        id="hypeman",
        name="The Hypeman",
        tagline="Maximum volume, maximum confidence.",
        prompt_addon="Add an over-the-top hype one-liner in a field called persona_message.",
        render=_hypeman,
    ),
}


def get_persona(persona_id: str) -> Persona:
    if persona_id not in PERSONAS:
        valid = ", ".join(PERSONAS)
        raise ValueError(f"unknown persona '{persona_id}'. Choose one of: {valid}")
    return PERSONAS[persona_id]
