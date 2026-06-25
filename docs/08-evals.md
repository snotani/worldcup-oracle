# 08 · Evals (the part tutorials skip)

**Goal:** turn "it feels smart" into numbers — and a bar it has to clear.

## On-camera
- Open [`spec/EVAL_SPEC.md`](../spec/EVAL_SPEC.md): accuracy, Brier, log loss, calibration, and
  the pass thresholds.
- Run the backtest:

```bash
cd backend && source .venv/bin/activate
oracle eval --mock            # offline demo
oracle eval                   # live (after matches finish)
```

Expected: a table of the agent vs `coin_flip`, `home_prior`, `form_model`.

## Talking points
- Accuracy = how often it's right. Brier / log loss = whether its probabilities are honest
  (lower is better).
- The agent has to beat a coin flip and match a sensible form model — otherwise it's not earning
  its keep.
- Always say `N`: early-tournament samples are small and noisy.

## Honest track for the live tournament
Predict before kickoff, then record the real result and score with no hindsight:

```bash
oracle predict <match_id>                 # before kickoff
oracle results <match_id> --auto          # after full time
oracle leaderboard                        # scored, no cheating
```

## What to show next
The payoff — `09-results.md`.
