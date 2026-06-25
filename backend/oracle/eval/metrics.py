"""Prediction metrics: the numbers that go on the scoreboard.

What: Accuracy, multiclass Brier score, log loss, and calibration over a set of predictions.
Why: These turn "the agent feels good" into "the agent is right 64% of the time with a Brier
of 0.58." Quantitative evals are the whole point of the teaching story (and the content hook).
How it fits: `backtest.py` and the CLI feed prediction samples in; the dashboard renders the
summaries out.
On camera: "Accuracy tells you how often it's right. Brier and log loss tell you whether the
probabilities are honest. Lower is better for both."
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

_CLASSES = ("home", "draw", "away")


@dataclass
class EvalSample:
    """One scored prediction: the probabilities, the pick, and what actually happened."""

    probs: dict[str, float]
    predicted: str
    actual: str


@dataclass
class CalibrationBin:
    lower: float
    upper: float
    count: int
    avg_confidence: float
    accuracy: float


@dataclass
class MetricSummary:
    """All headline metrics for one predictor."""

    name: str
    n: int
    accuracy: float
    brier: float
    log_loss: float
    calibration: list[CalibrationBin] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "n": self.n,
            "accuracy": round(self.accuracy, 4),
            "brier": round(self.brier, 4),
            "log_loss": round(self.log_loss, 4),
            "calibration": [
                {
                    "lower": round(b.lower, 2),
                    "upper": round(b.upper, 2),
                    "count": b.count,
                    "avg_confidence": round(b.avg_confidence, 4),
                    "accuracy": round(b.accuracy, 4),
                }
                for b in self.calibration
            ],
        }


def accuracy(samples: list[EvalSample]) -> float:
    if not samples:
        return 0.0
    return sum(1 for s in samples if s.predicted == s.actual) / len(samples)


def brier_score(samples: list[EvalSample]) -> float:
    """Multiclass Brier: mean squared error between the prob vector and the one-hot result."""
    if not samples:
        return 0.0
    total = 0.0
    for s in samples:
        for c in _CLASSES:
            y = 1.0 if s.actual == c else 0.0
            total += (s.probs.get(c, 0.0) - y) ** 2
    return total / len(samples)


def log_loss(samples: list[EvalSample], eps: float = 1e-12) -> float:
    """Negative log-likelihood of the actual outcomes under the predicted probabilities."""
    if not samples:
        return 0.0
    total = 0.0
    for s in samples:
        p = min(1.0, max(eps, s.probs.get(s.actual, 0.0)))
        total += -math.log(p)
    return total / len(samples)


def calibration(samples: list[EvalSample], bins: int = 5) -> list[CalibrationBin]:
    """Bucket predictions by confidence and compare confidence to empirical accuracy."""
    buckets: list[list[EvalSample]] = [[] for _ in range(bins)]
    for s in samples:
        conf = max(s.probs.values()) if s.probs else 0.0
        idx = min(bins - 1, int(conf * bins))
        buckets[idx].append(s)
    out: list[CalibrationBin] = []
    for i, bucket in enumerate(buckets):
        lower, upper = i / bins, (i + 1) / bins
        if not bucket:
            out.append(CalibrationBin(lower, upper, 0, 0.0, 0.0))
            continue
        avg_conf = sum(max(s.probs.values()) for s in bucket) / len(bucket)
        out.append(CalibrationBin(lower, upper, len(bucket), avg_conf, accuracy(bucket)))
    return out


def summarize(name: str, samples: list[EvalSample]) -> MetricSummary:
    """Compute all metrics for one predictor."""
    return MetricSummary(
        name=name,
        n=len(samples),
        accuracy=accuracy(samples),
        brier=brier_score(samples),
        log_loss=log_loss(samples),
        calibration=calibration(samples),
    )
