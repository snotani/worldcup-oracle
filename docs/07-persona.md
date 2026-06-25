# 07 · The persona (Angle C)

**Goal:** show that voice is a thin layer over a solid agent.

## On-camera
- Open [`backend/oracle/personas/personas.py`](../backend/oracle/personas/personas.py). Three
  voices: The Gaffer, The Professor, The Hypeman.
- Run the same prediction, now with a mouth:

```bash
cd backend && source .venv/bin/activate
oracle predict 1001 --mock --persona gaffer
oracle predict 1001 --mock --persona hypeman
```

Expected: identical probabilities, very different delivery.

## Talking points
- "Same numbers. The personality is a wrapper — which proves the agent underneath is solid."
- This is the most shareable angle: screenshots of the trash talk travel.

## What to show next
Proving it works — `08-evals.md`.
