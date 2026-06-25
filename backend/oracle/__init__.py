"""The Oracle: an AI agent that predicts FIFA World Cup 2026 matches.

Public surface re-exported for convenience.
"""

from .schema import MatchContext, MatchPrediction, Probabilities, StoredPrediction, TeamForm

__all__ = [
    "MatchContext",
    "MatchPrediction",
    "Probabilities",
    "StoredPrediction",
    "TeamForm",
]
