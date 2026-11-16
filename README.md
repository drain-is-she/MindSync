# MindSync AI

A local wellbeing prototype combining FastAPI, SQLite, synthetic telemetry,
Streamlit, and a LangGraph agent with cited NHS guidance. All measurements are
**SIMULATED DATA**. This application does not diagnose conditions.

## Start

Python 3.11+:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn mindsync.platform.api:app --host 127.0.0.1 --port 8000
```

In another terminal with that environment activated:

```bash
streamlit run frontend/app.py --server.address 127.0.0.1
```

Optionally publish new simulated readings:

```bash
python -m mindsync.simulator.publisher --profile student_a
```

Startup migrates `runtime/mindsync.db` and seeds three synthetic profiles with
seven days of history. Student A models exam-week sleep changes, B physical
activity, and C missing/noisy readings. Existing data is retained. Use `--count 1`
to send a single telemetry packet. The dashboard offers trends, mood check-ins,
chat, citations, tool traces, and an A/B/C comparison.

## Agent and experiment modes

The default `MINDSYNC_AGENT=real` selects the implemented LangGraph workflow:
context collection → local retrieval → grounded response. It uses whole-word
retrieval over three curated, source-linked NHS guidance summaries and generates
deterministic exercises. It requires **no API key or network service**. This is a
small retrieval-based assistant, not a general-purpose LLM or semantic vector RAG.
Ask about sleep, worries/exams, or breathing. Unmatched questions receive an
honest fallback; diagnostic and medication requests are declined.

| Mode | Context used by the agent | Consent |
| --- | --- | --- |
| A: Text only | Message and prior topic in this scope | Not required |
| B: Current vitals | Message plus fresh synthetic reading | Required |
| C: Full context | Message, fresh reading, seven-day summary | Required |

Exercises are selected from the message, never inferred from physiological
values. Sources and tool traces correspond to actual retrieval and context calls.
A topic-only memory supports follow-ups such as “continue”; it expires after 30
minutes and is limited to 256 session scopes. It is isolated by session, profile,
mode, and consent. No conversation text or vitals are retained in agent memory.
Memory is process-local and resets on restart; use one backend worker for continuity.

For the original platform-only stub, explicitly set `MINDSYNC_AGENT=mock`.
Configuration is shown in `.env.example`; export values in your shell because
that file is not automatically loaded. `MINDSYNC_SEED_DEMO=false` disables seeding.

## Validate

```bash
pytest -q
python -m mindsync.evaluation
pip check
```

Tests cover storage, simulator retries, consent restrictions, real-agent retrieval,
citations, topic isolation/expiry, missing tools, urgent routing, HTTP integration,
and Streamlit interaction. The offline evaluation checks 15 prompt/mode cases and
exits nonzero on failure. CI runs tests and evaluation on Python 3.11 and 3.13.
These are engineering checks, not a clinical efficacy assessment.

## Boundaries

Run locally: there is no real-user authentication or production hosting setup.
Mood notes are stored in local SQLite. Synthetic vitals do not establish a person's
mental or physical condition. The urgent-support gate uses conservative English
phrase matching and can miss paraphrases or other languages; it is not clinically
validated. It directs explicit urgent disclosures to human help without contacting
anyone automatically. Source summaries were checked on 2026-11-16; see
`src/mindsync/ai/knowledge.py` for exact provenance and `docs/agent.md` for design.

The original developer handoff and workflow documents describe the archived
platform development history. This README and `docs/agent.md` describe the
completed local integration.
