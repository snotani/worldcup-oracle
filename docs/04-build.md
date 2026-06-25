# 04 · Build the agent loop

**Goal:** show the entire agent in one screen, then watch it run.

## On-camera
- Open [`backend/oracle/agent.py`](../backend/oracle/agent.py). Point at the six steps:
  gather_data → build_prompt → call_model → parse_validate → (apply_persona) → store.
- Run it with the trace visible:

```bash
cd backend && source .venv/bin/activate
oracle predict 1001 --mock --explain
```

Expected: a prediction table, then a numbered run trace showing each step and its timing.

## Talking points
- "This is the whole agent. Six steps. Nothing hidden."
- The trace (`oracle/trace.py`) is what makes it explainable — it's not a black box.
- The model is called behind one interface (`oracle/models.py`), which sets up the battle later.

## What to show next
The tools that feed it — `05-tools-data.md`.
