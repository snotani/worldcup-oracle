"""Observable run trace: the agent narrating its own steps.

What: A lightweight, ordered, timestamped record of every step the agent takes
(gather_data -> build_prompt -> call_model -> parse -> validate -> store).
Why: For content, the steps ARE the story. This makes the agent's reasoning process visible
and recordable instead of a black box. It doubles as debugging/observability.
How it fits: `agent.py` opens a RunTrace and logs each phase; the CLI `--explain` flag prints
it as clean numbered steps; the dashboard replays it visually.
On camera: "Watch the agent think: step one it gathers data, step two it builds the prompt,
step three it calls the model, then it parses and validates the answer."
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

_console = Console()


class TraceStep:
    """One completed step in the agent pipeline."""

    def __init__(
        self,
        index: int,
        name: str,
        detail: str,
        data: dict[str, Any],
        started_at: datetime,
        duration_ms: float,
    ) -> None:
        self.index = index
        self.name = name
        self.detail = detail
        self.data = data
        self.started_at = started_at
        self.duration_ms = duration_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "detail": self.detail,
            "data": self.data,
            "started_at": self.started_at.isoformat(),
            "duration_ms": self.duration_ms,
        }


class _StepTimer:
    """Context manager that times a step and appends it to its trace on exit."""

    def __init__(self, trace: RunTrace, name: str, detail: str, data: dict[str, Any]) -> None:
        self._trace = trace
        self._name = name
        self._detail = detail
        self._data = data
        self._start = 0.0
        self._dt: datetime | None = None

    def __enter__(self) -> _StepTimer:
        self._start = time.perf_counter()
        self._dt = datetime.now(UTC)
        return self

    def detail(self, text: str) -> None:
        """Update the human-readable detail once the step's outcome is known."""
        self._detail = text

    def add(self, **data: Any) -> None:
        """Attach structured data discovered during the step."""
        self._data.update(data)

    def __exit__(self, *exc: Any) -> None:
        duration = round((time.perf_counter() - self._start) * 1000, 1)
        self._trace._append(
            TraceStep(
                index=len(self._trace.steps) + 1,
                name=self._name,
                detail=self._detail,
                data=self._data,
                started_at=self._dt or datetime.now(UTC),
                duration_ms=duration,
            )
        )


class RunTrace:
    """An ordered list of steps for a single agent run."""

    def __init__(self, label: str = "", model_id: str | None = None) -> None:
        self.trace_id = uuid.uuid4().hex[:12]
        self.label = label
        self.model_id = model_id
        self.started_at = datetime.now(UTC)
        self.steps: list[TraceStep] = []

    def _append(self, step: TraceStep) -> None:
        self.steps.append(step)

    def step(self, name: str, detail: str = "", **data: Any) -> _StepTimer:
        """Time a step. Use as `with trace.step('call_model') as s: ...`."""
        return _StepTimer(self, name, detail, data)

    def record(self, name: str, detail: str = "", duration_ms: float = 0.0, **data: Any) -> None:
        """Record an already-completed step (when timing isn't needed)."""
        self._append(
            TraceStep(
                index=len(self.steps) + 1,
                name=name,
                detail=detail,
                data=data,
                started_at=datetime.now(UTC),
                duration_ms=round(duration_ms, 1),
            )
        )

    @property
    def total_ms(self) -> float:
        return round(sum(s.duration_ms for s in self.steps), 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "label": self.label,
            "model_id": self.model_id,
            "started_at": self.started_at.isoformat(),
            "total_ms": self.total_ms,
            "steps": [s.to_dict() for s in self.steps],
        }

    def render(self) -> None:
        """Pretty-print the trace for screen recording (used by CLI --explain)."""
        table = Table(show_header=True, header_style="bold", expand=True)
        table.add_column("#", width=3, justify="right")
        table.add_column("Step", style="bold")
        table.add_column("What happened")
        table.add_column("ms", justify="right", width=8)
        for s in self.steps:
            table.add_row(str(s.index), s.name, s.detail, f"{s.duration_ms:.0f}")
        title = f"Oracle run trace  ({self.label or self.trace_id})"
        if self.model_id:
            title += f"  -  model: {self.model_id}"
        _console.print(Panel(table, title=title, subtitle=f"total {self.total_ms:.0f} ms"))
