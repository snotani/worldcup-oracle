# 06 · Models & the battle (Angle B)

**Goal:** show that swapping the model is one parameter — then make them fight.

## On-camera
- Open [`backend/oracle/models.py`](../backend/oracle/models.py). Show:
  - The Cursor SDK call (`Agent.prompt`) — one `CURSOR_API_KEY`, the model id is swappable.
  - `BATTLE_REGISTRY`: friendly name → model id.
- List your available models (live):

```bash
cd backend && source .venv/bin/activate
oracle models
```

- Run the battle:

```bash
oracle battle 1001 --mock                       # offline demo
oracle battle 1001 --models claude,gpt,gemini,grok   # live
```

Expected: one table, each model's pick + probabilities for the same match.

## Talking points
- "Same spec, same prompt, same data — only the model changes. That's the whole battle."
- Important nuance: this uses the Cursor **Agent SDK**, not a raw model API. One key, your
  existing Cursor model access.

## What to show next
Personality — `07-persona.md`.
