"""Data tools: how the agent learns about a match before predicting.

These are the agent's "tools" in the agent-design sense: functions that fetch real-world
context (fixtures, form, head-to-head) which the orchestrator feeds into the prompt.
"""

from .api_football import DataProvider, get_provider

__all__ = ["DataProvider", "get_provider"]
