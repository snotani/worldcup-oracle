# 05 · Tools & data (what the agent knows)

**Goal:** show the "tools" — the data the agent gathers before predicting.

## On-camera
- Open [`backend/oracle/tools/espn.py`](../backend/oracle/tools/espn.py) (the live source).
  Show `get_match_context` assembling form + goals + head-to-head into a clean brief.
- Show the live fixtures list:

```bash
cd backend && source .venv/bin/activate
oracle fixtures --status NS        # live upcoming 2026 matches (ESPN, no key)
oracle fixtures --status FT        # finished 2026 matches with real scores
```

- Mention caching: `tools/cache.py` stores the one ESPN request so a whole backtest re-reads
  from disk instead of the network.

## Talking points
- An agent is only as good as its context. These tools are the agent's eyes.
- Live data is real 2026 World Cup from ESPN's public API — no key needed; ESPN even ships a
  recent-form string per team.
- Same shape offline: `--mock` (or `USE_MOCK_DATA=1`) runs the whole thing with no network.
- API-Football is also supported (`DATA_SOURCE=api_football`) but its free tier is 2022–2024.

## What to show next
The model layer and the battle — `06-models-battle.md`.
