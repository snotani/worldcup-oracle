# 02 · The spec (write it before the code)

**Goal:** show that we design the contract first — this is the part most tutorials skip.

## The big idea (say this)
"Before writing any agent logic, I decided exactly what goes in and what must come out. That one
decision is what makes the whole thing testable."

## On-camera
- Open [`spec/AGENT_SPEC.md`](../spec/AGENT_SPEC.md). Walk through:
  - Inputs (the `MatchContext`).
  - The output contract (probabilities that sum to 1, an argmax pick, a confidence, a rationale).
  - Tools, guardrails, success criteria.
- Open [`spec/EVAL_SPEC.md`](../spec/EVAL_SPEC.md). Point at the metrics and the pass thresholds:
  "beat a coin flip on accuracy, match the form model on Brier."

## Talking points
- A spec turns "make an AI predict football" into a checklist you can satisfy and verify.
- The output schema is the agent's contract; everything downstream trusts it.

## What to show next
How the spec becomes code — `03-spec-driven-dev.md`.
