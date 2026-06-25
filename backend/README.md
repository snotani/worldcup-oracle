# Oracle backend

Python core for The Oracle: data tools, the agent loop, model adapter (Cursor SDK), eval
harness, CLI, and FastAPI server.

## Setup

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Set `CURSOR_API_KEY` and `API_FOOTBALL_KEY` in the repo-root `.env` (see `.env.example`).

## Try it offline (no keys, no network)

```bash
oracle predict 1001 --mock --explain     # one prediction + the run trace
oracle battle 1001 --mock                # all models on one match
oracle eval --mock                       # backtest vs baselines
oracle predict 1001 --mock --persona gaffer
oracle export --mock                     # build the dashboard JSON
```

## Live

Drop `--mock` to use real Cursor models and live API-Football data:

```bash
oracle models                            # list available model ids
oracle fixtures --status NS
oracle predict <match_id> --explain
oracle battle <match_id> --models claude,gpt,gemini,grok
oracle eval
uvicorn oracle.api:app --reload          # serve the dashboard API
```

## Layout

- `oracle/schema.py` - the prediction contract (Pydantic)
- `oracle/tools/` - API-Football data tools + cache (the agent's tools)
- `oracle/models.py` - Cursor SDK adapter + mock backend + model registry
- `oracle/agent.py` - the orchestration loop (emits a run trace)
- `oracle/personas/` - persona voices (Angle C)
- `oracle/eval/` - metrics, baselines, backtest (Angle A)
- `oracle/dashboard.py` - builds the dashboard payload
- `oracle/cli.py` - the CLI; `oracle/api.py` - FastAPI server
- `oracle/trace.py` - observable step-by-step run trace
