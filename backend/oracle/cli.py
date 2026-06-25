"""Command-line interface: every agent capability, demoable on camera.

What: A Typer CLI exposing predict / battle / eval / persona / fixtures / results / export.
Why: A clean CLI is the easiest thing to screen-record and the simplest way to drive each of
the three content angles. The `--explain` flag prints the run trace as numbered steps.
How it fits: Wraps `agent.py`, `eval/`, and `dashboard.py`. `oracle export` feeds the Next.js
dashboard.
On camera: "One command predicts a match. Add --explain and you watch every step. Add --battle
and the models fight."
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .agent import predict_match
from .config import get_settings
from .dashboard import build_payload
from .eval.backtest import run_backtest, score_stored_predictions
from .models import BATTLE_REGISTRY, get_model_backend
from .personas import PERSONAS
from .store import Store
from .tools import get_provider

app = typer.Typer(help="The Oracle - World Cup 2026 prediction agent.", no_args_is_help=True)
console = Console()


def _settings(mock: bool):
    """Return settings, forcing offline mock data when --mock is passed."""
    s = get_settings()
    return s.model_copy(update={"use_mock_data": True}) if mock else s

# frontend/public/data/dashboard.json relative to this file.
_DEFAULT_EXPORT = (
    Path(__file__).resolve().parents[2] / "frontend" / "public" / "data" / "dashboard.json"
)


def _outcome_label(outcome: str, home: str, away: str) -> str:
    return {"home": home, "away": away, "draw": "Draw"}.get(outcome, outcome)


@app.command()
def fixtures(
    status: str = typer.Option("", help="Filter: NS (upcoming) or FT (finished)"),
    mock: bool = typer.Option(False, "--mock", help="Use the offline mock data"),
) -> None:
    """List World Cup fixtures."""
    provider = get_provider(_settings(mock))
    rows = provider.list_fixtures(status=status or None)
    table = Table(title=f"Fixtures{f' ({status})' if status else ''}")
    table.add_column("ID", justify="right")
    table.add_column("Status")
    table.add_column("Kickoff (UTC)")
    table.add_column("Match")
    table.add_column("Score")
    for f in rows:
        score = (
            f"{f['home_goals']}-{f['away_goals']}"
            if f["home_goals"] is not None
            else "-"
        )
        table.add_row(
            str(f["match_id"]),
            f["status"] or "",
            (f["kickoff_utc"] or "")[:16],
            f"{f['home_team']} vs {f['away_team']}",
            score,
        )
    console.print(table)


@app.command()
def predict(
    match_id: int,
    model: str = typer.Option("", help="Model id (default from settings, e.g. 'auto')"),
    persona: str = typer.Option("", help=f"Persona: {', '.join(PERSONAS)}"),
    explain: bool = typer.Option(False, "--explain", help="Print the step-by-step run trace"),
    mock: bool = typer.Option(False, "--mock", help="Use the offline mock model"),
    save: bool = typer.Option(True, help="Persist the prediction"),
) -> None:
    """Predict a single match (Angle A core; add --persona for Angle C)."""
    stored, trace = predict_match(
        match_id,
        model_id=model or None,
        persona=persona or None,
        settings=_settings(mock),
        mock_model=mock,
        save=save,
    )
    _print_prediction(stored)
    if explain:
        trace.render()


@app.command()
def battle(
    match_id: int,
    models: str = typer.Option(
        ",".join(BATTLE_REGISTRY), help="Comma-separated friendly names or ids"
    ),
    explain: bool = typer.Option(False, "--explain", help="Print each model's run trace"),
    mock: bool = typer.Option(False, "--mock", help="Use the offline mock model"),
    save: bool = typer.Option(True, help="Persist predictions"),
) -> None:
    """Run the same match through multiple models and compare (Angle B)."""
    names = [m.strip() for m in models.split(",") if m.strip()]
    settings = _settings(mock)
    table = Table(title=f"Model Battle - match {match_id}")
    table.add_column("Model")
    table.add_column("Pick")
    table.add_column("H/D/A")
    table.add_column("Score")
    table.add_column("Conf", justify="right")
    traces = []
    for name in names:
        model_id = BATTLE_REGISTRY.get(name, name)
        stored, trace = predict_match(
            match_id, model_id=model_id, settings=settings, mock_model=mock, save=save
        )
        p = stored.prediction.probabilities
        table.add_row(
            name,
            _outcome_label(stored.prediction.predicted_outcome, stored.home_team, stored.away_team),
            f"{p.home:.0%}/{p.draw:.0%}/{p.away:.0%}",
            stored.prediction.predicted_score or "-",
            f"{stored.prediction.confidence:.0%}",
        )
        traces.append(trace)
    console.print(table)
    if explain:
        for t in traces:
            t.render()


@app.command(name="eval")
def eval_cmd(
    model: str = typer.Option("", help="Model id to evaluate"),
    mock: bool = typer.Option(False, "--mock", help="Use the offline mock model"),
    limit: int = typer.Option(0, help="Limit number of finished matches (0 = all)"),
) -> None:
    """Backtest the agent over finished matches vs baselines (Angle A scoreboard)."""
    report = run_backtest(
        model or None, settings=_settings(mock), mock_model=mock, limit=limit or None
    )
    table = Table(title=f"Backtest over {report.n_matches} finished matches")
    table.add_column("Predictor")
    table.add_column("N", justify="right")
    table.add_column("Accuracy", justify="right")
    table.add_column("Brier", justify="right")
    table.add_column("Log loss", justify="right")
    for s in report.summaries:
        style = "bold green" if s.name.startswith("agent:") else ""
        table.add_row(
            s.name,
            str(s.n),
            f"{s.accuracy:.1%}",
            f"{s.brier:.3f}",
            f"{s.log_loss:.3f}",
            style=style,
        )
    console.print(table)


@app.command()
def results(
    match_id: int,
    outcome: str = typer.Argument("", help="home|draw|away (omit with --auto)"),
    score: str = typer.Option("", help="Final score e.g. 2-1"),
    auto: bool = typer.Option(False, "--auto", help="Fetch the real result from the data API"),
    mock: bool = typer.Option(False, "--mock", help="Use the offline mock data with --auto"),
) -> None:
    """Record the actual result of a match so predictions can be scored."""
    if auto:
        res = get_provider(_settings(mock)).get_result(match_id)
        if res is None:
            console.print(f"[yellow]No finished result available for match {match_id}.[/]")
            raise typer.Exit(1)
        outcome, score = res
    if outcome not in {"home", "draw", "away"}:
        console.print("[red]Provide an outcome (home|draw|away) or use --auto.[/]")
        raise typer.Exit(1)
    with Store() as store:
        n = store.set_result(match_id, outcome, score or None)
    console.print(f"Recorded {outcome} ({score or 'n/a'}) for match {match_id}; updated {n} rows.")


@app.command()
def leaderboard() -> None:
    """Show stored-prediction accuracy per model for finished matches."""
    summaries = score_stored_predictions()
    if not summaries:
        console.print("[yellow]No completed predictions yet. Run predictions, then `results`.[/]")
        return
    table = Table(title="Live model leaderboard (stored predictions)")
    table.add_column("Model")
    table.add_column("N", justify="right")
    table.add_column("Accuracy", justify="right")
    table.add_column("Brier", justify="right")
    for s in sorted(summaries, key=lambda x: (-x.accuracy, x.brier)):
        table.add_row(s.name, str(s.n), f"{s.accuracy:.1%}", f"{s.brier:.3f}")
    console.print(table)


@app.command()
def models() -> None:
    """List model ids available to your account (via the Cursor SDK)."""
    backend = get_model_backend()
    try:
        ids = backend.list_available_models()
    except Exception as exc:  # noqa: BLE001 - surface any SDK/auth error cleanly
        console.print(f"[red]Could not list models: {exc}[/]")
        raise typer.Exit(1) from exc
    table = Table(title="Available models")
    table.add_column("Model id")
    for mid in ids:
        table.add_row(mid)
    console.print(table)


@app.command()
def export(
    out: Path = typer.Option(_DEFAULT_EXPORT, help="Output JSON path for the dashboard"),
    mock: bool = typer.Option(False, "--mock", help="Use the offline mock model"),
    persona: str = typer.Option("gaffer", help=f"Persona for cards: {', '.join(PERSONAS)}"),
    upcoming_limit: int = typer.Option(6, help="Upcoming fixtures to include (battle + cards)"),
    finished_limit: int = typer.Option(8, help="Recent finished matches to score"),
    models: str = typer.Option(
        ",".join(BATTLE_REGISTRY), help="Comma-separated battle models (friendly names or ids)"
    ),
    workers: int = typer.Option(6, help="Concurrent model calls"),
) -> None:
    """Build the dashboard JSON payload (feeds the Next.js frontend).

    Live model calls are the slow part: roughly
    (finished_limit + upcoming_limit) x len(models) predictions. Start small.
    """
    battle = [m.strip() for m in models.split(",") if m.strip()]
    n_calls = (finished_limit + upcoming_limit) * len(battle)
    console.print(
        f"[dim]Running ~{n_calls} model predictions "
        f"({'mock' if mock else 'live'}, {workers} workers)...[/]"
    )
    payload = build_payload(
        settings=_settings(mock),
        mock_model=mock,
        persona=persona,
        battle=battle,
        upcoming_limit=upcoming_limit,
        finished_limit=finished_limit,
        workers=workers,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    console.print(
        f"Wrote dashboard payload to [bold]{out}[/] "
        f"({len(payload['battle_matches'])} upcoming, {payload['scoreboard']['n_matches']} scored, "
        f"{len(payload['leaderboard'])} models)."
    )


def _print_prediction(stored) -> None:
    p = stored.prediction.probabilities
    table = Table(title=f"{stored.home_team} vs {stored.away_team}  (match {stored.match_id})")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Model", stored.model_id)
    pick_label = _outcome_label(
        stored.prediction.predicted_outcome, stored.home_team, stored.away_team
    )
    table.add_row("Pick", pick_label)
    table.add_row("Probabilities", f"H {p.home:.0%} / D {p.draw:.0%} / A {p.away:.0%}")
    table.add_row("Predicted score", stored.prediction.predicted_score or "-")
    table.add_row("Confidence", f"{stored.prediction.confidence:.0%}")
    table.add_row("Rationale", stored.prediction.rationale)
    if stored.persona_message:
        table.add_row(f"[{stored.persona}]", stored.persona_message)
    console.print(table)


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
