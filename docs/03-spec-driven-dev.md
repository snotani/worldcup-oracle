# 03 · Spec-driven development

**Goal:** show the spec turning directly into typed code.

## On-camera
- Open [`backend/oracle/schema.py`](../backend/oracle/schema.py). Map it line-by-line to the
  spec:
  - `Probabilities` with the "must sum to 1" validator → the spec invariant, in code.
  - `MatchPrediction` with "outcome equals argmax" → the spec invariant, enforced.
- Run a quick proof that the contract bites:

```bash
cd backend && source .venv/bin/activate
python -c "from oracle.schema import Probabilities; Probabilities(home=0.9, draw=0.9, away=0.9)"
```

Expected: a validation error — bad probabilities can't even be constructed.

## Talking points
- The schema is executable spec. If the model returns garbage, validation catches it.
- This is why we wrote the spec first: the types fall out of it.

## What to show next
Building the agent loop — `04-build.md`.
