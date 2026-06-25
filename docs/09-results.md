# 09 · Results (the payoff)

**Goal:** the recordable dashboard moment + the ongoing-content engine.

## On-camera
- Build the payload and open the dashboard:

```bash
cd backend && source .venv/bin/activate && oracle export --mock
cd ../frontend && npm run dev
# open http://localhost:3000
```

- Walk the three tabs:
  - **A — Beat the bookies:** the scoreboard, agent vs baselines.
  - **B — Model battle:** the leaderboard + each model's picks; expand a run trace.
  - **C — The persona:** the shareable cards.

## Talking points
- "Everything here came from one payload the agent produced."
- Expand a trace on camera: "this is the agent thinking — six steps, every time."

## The content engine (why this keeps giving)
During the tournament, regenerate and post:
```bash
oracle export        # live data + models
```
Every matchday is a new post: "Day X — the Oracle is N/M correct, and Claude just overtook GPT."

## Wrap line
"Problem, spec, build, evals, results. That's how you actually ship an AI agent."
