# Evaluation Spec — The Oracle

How we prove the agent is actually any good. Written before the eval code.

## Dataset

- **Backtest set**: all finished World Cup fixtures (`status == FT`) available from the data
  provider. Each fixture yields one labelled example: the pre-match context (input) and the
  real outcome (label).
- **No leakage**: the agent only ever sees pre-match `MatchContext`. Results are used solely to
  score, never to predict.
- **Reproducibility**: API responses are cached and completed matches are snapshotted, so a
  backtest gives the same numbers on reruns. Offline mock data ships for tests/CI.

## Predictors compared

On the exact same fixtures:

- `agent:<model_id>` — the Oracle (per model, enabling the battle).
- `coin_flip` — uniform 1/3, 1/3, 1/3.
- `home_prior` — fixed home-advantage prior (0.45 / 0.27 / 0.28).
- `form_model` — a respectable non-AI predictor from recent-form points + home advantage.

## Metrics (see `backend/oracle/eval/metrics.py`)

- **Accuracy** — fraction of matches where the argmax pick equals the actual outcome. Intuitive,
  but ignores confidence.
- **Brier score** (multiclass) — mean squared error between the probability vector and the
  one-hot result. Lower is better. Rewards honest probabilities.
- **Log loss** — negative log-likelihood of the actual outcome. Lower is better. Punishes
  confident mistakes harshly.
- **Calibration** — predictions bucketed by confidence; compares stated confidence to empirical
  accuracy per bucket. A well-calibrated agent that says "70%" is right ~70% of the time.

## Pass thresholds (success criteria)

1. `accuracy(agent) > accuracy(coin_flip)`
2. `brier(agent) <= brier(form_model)`

If both hold over a non-trivial sample, the agent is "earning its keep."

## Two evaluation modes

- **Backtest** (`oracle eval`) — generate predictions for already-finished matches and score
  immediately. Used for the scoreboard and the model-battle standings.
- **Live scoring** (`oracle leaderboard`) — score the real predictions stored before kickoff,
  once `oracle results <match_id> --auto` records the actual outcome. This is the honest,
  no-hindsight track during the live tournament.

## Caveats to state on camera

- Small samples early in the tournament make all metrics noisy; report `N` alongside every
  number.
- The mock/offline numbers are illustrative only (synthetic data), clearly badged as "demo data"
  in the dashboard.
