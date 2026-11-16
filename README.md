# MindSync AI — Developer 1 platform

FastAPI + SQLite + synthetic telemetry + Streamlit, runnable without an LLM or
Developer 2 code. All measurements are **SIMULATED DATA**. This is a local,
non-diagnostic wellbeing prototype.

## Run

Python 3.11+ is supported. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn mindsync.platform.api:app --host 127.0.0.1 --port 8000
```

In a second terminal with the same environment activated:

```bash
streamlit run frontend/app.py
```

In an optional third terminal:

```bash
python -m mindsync.simulator.publisher --profile student_a
```

Startup migrates `runtime/mindsync.db` and seeds three synthetic profiles.
Student A models exam-week reduced sleep; B models physical activity; C models
missing/noisy readings and a stale sensor. These describe scenarios, not diagnoses.
Use `--count 1` for a single telemetry packet. Ctrl-C stops the publisher.

Configuration environment variables are listed in `.env.example`. The file is a
template and is not loaded automatically; export values in your shell.
`MINDSYNC_SEED_DEMO=false` disables automatic demo creation.
`python -m mindsync.simulator.seed` seeds explicitly and is idempotent.
For reproducible fixtures call `seed(path, now=<fixed aware datetime>, seed_value=42)`.
To obtain a fresh demo later, use a new `MINDSYNC_DB_PATH`; existing data is retained.

The dashboard includes current readings, pulse and sleep history, mood check-in,
chat, citations, tool traces, and three independent A/B/C requests. B and C require
consent. A never receives vitals through the context provider. The mock is clearly
labelled, performs real context calls, and does not fabricate RAG sources.

## Test

```bash
pytest -q
```

Tests run on temporary SQLite databases and use no external LLM. See
`docs/contracts.md` for the shared types, API semantics, and Developer 2 entry point.
After Developer 2 is merged, set `MINDSYNC_AGENT=real` and restart; no contract
changes should be needed. AI dependencies must be added in coordination with that
implementation. Real-agent functionality is not included in this platform branch.

## Scope and limits

The safety gate routes explicit urgent English disclosures to human assistance,
bypassing the ordinary agent. It is conservative phrase matching, not clinically
validated, and cannot guarantee detection. Synthetic vital values never determine
the safety route. See `docs/architecture.md` for boundaries and limitations.
This demo has no authentication and should run locally.

The upstream repository was empty. The initial contract and implementation are
on `feat/platform-iot-ui`; nothing has been pushed to main. Coordinate the foundation
merge with Developer 2 before treating the contract as shared and frozen.
