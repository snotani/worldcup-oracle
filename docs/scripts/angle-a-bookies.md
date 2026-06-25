# Shooting script — Angle A: "I built an AI that out-predicts the bookies"

Target length: 60–90s. Reuses steps 01, 02, 08, 09.

## Cold open (hook, 0–5s)
On camera: "I built an AI agent to predict the World Cup — and then I made it prove it."

## Beat 1 — the problem (5–15s)
- Reference [`01-problem.md`](../01-problem.md).
- Line: "Anyone can guess. I wanted something I could actually grade."

## Beat 2 — the contract (15–30s)
- Show [`spec/AGENT_SPEC.md`](../../spec/AGENT_SPEC.md) output schema.
- Line: "Probabilities that sum to one. A pick. A confidence. Now it's testable."

## Beat 3 — the receipts (30–55s)
- Terminal: `oracle eval --mock` (or live).
- Point at the agent row beating `coin_flip` and matching `form_model` on Brier.
- Line: "Accuracy beats a coin flip. And its probabilities are honest — that's the Brier score."

## Beat 4 — the scoreboard (55–75s)
- Dashboard tab A. Show the match-by-match hits.
- Line: "And this updates every matchday."

## CTA
"Follow — I'm scoring it live all tournament."

## B-roll checklist
- [ ] Schema scroll
- [ ] `oracle eval` table
- [ ] Dashboard tab A
- [ ] One trace expanded
