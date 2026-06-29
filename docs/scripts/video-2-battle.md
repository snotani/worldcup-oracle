# Shooting script — Video 2: "Top 5 AI models fight to predict the World Cup"

Target length: 45–75s. Reuses steps 03 (spec), 04 (build).

## Cold open (0–5s)
"I made the five best AI models — Claude, ChatGPT, Gemini, Grok and Composer — fight to
predict the whole World Cup bracket."

## Beat 1 — the setup (5–20s)
- Show [`backend/oracle/models.py`](../../backend/oracle/models.py) `BATTLE_REGISTRY`.
- Line: "Same bracket, same data, same rules. The only thing that changes is the model id —
  it runs on the Cursor Agent SDK, so it's one key and the models I already have."

## Beat 2 — the brackets (20–55s)
- Dashboard, **Model Battle** tab. The five champion cards line up across the top.
- Tap between models and let each path play. "Three of them crown one nation, two back
  another — same inputs, different brains."
- Land on the consensus card: title votes, how often they agree in the first round, and the
  matches where they flat-out disagree.

## Beat 3 — the verdict (55–75s)
- Read the consensus champion and the biggest disagreement.
- CTA: "Which model do you trust? I'll grade them all when the real games are played."

## On camera / CLI alt
- `oracle simulate-battle --mock` prints every model's champion + the consensus in the terminal.

## B-roll checklist
- [ ] `BATTLE_REGISTRY` highlight + `oracle models`
- [ ] Five champion cards
- [ ] A model's path animating in its brand colour
- [ ] Consensus: votes + contested matches
