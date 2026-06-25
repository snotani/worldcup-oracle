# Shooting script — Angle B: "GPT vs Claude vs Gemini vs Grok predict the World Cup"

Target length: 60–90s. Reuses steps 03, 06, 09.

## Cold open (0–5s)
"I made four AI models fight over the World Cup. Same brain, different model. One leaderboard."

## Beat 1 — the trick (5–25s)
- Show [`backend/oracle/models.py`](../../backend/oracle/models.py) `BATTLE_REGISTRY`.
- Line: "Same spec, same prompt, same data. The only thing I change is this one line — the model."
- Nuance to say: "This runs on the Cursor Agent SDK — one key, the models I already have."

## Beat 2 — the battle (25–55s)
- Terminal: `oracle battle 1001 --models claude,gpt,gemini,grok` (live) or `--mock`.
- Read out where they disagree.

## Beat 3 — the leaderboard (55–80s)
- Dashboard tab B. Standings + each model's picks.
- Expand a run trace: "and you can see exactly how each one reasoned."

## CTA
"Who's your money on? I'm tracking it every matchday."

## B-roll checklist
- [ ] `BATTLE_REGISTRY` highlight
- [ ] `oracle models` list
- [ ] `oracle battle` table
- [ ] Dashboard tab B + trace expand
