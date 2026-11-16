# Platform validation

Validated locally on 2026-11-16 with Python 3.13.11 in `.venv`.
Python 3.11 was not installed, so that target runtime remains unverified.

`python -m pytest -q`: **34 passed, 0 failed**.

Coverage includes fresh/idempotent migrations and foreign keys; deterministic,
idempotent seeding; exact heart-rate and sleep statistics; empty/stale/missing
and future readings; valid telemetry, UTC normalization and duplicate handling;
invalid and non-finite readings; all three context capabilities and cross-profile
blocking; consent; unknown profiles; urgent agent bypass; mock chat and check-ins;
injected agents; failures/timeouts; Streamlit A/B/C sessions and mood form;
and visible frontend API errors.

One dependency deprecation warning was emitted: installed Starlette deprecates
its httpx-backed TestClient in favor of httpx2. All tests completed successfully.

Additional live smoke checks passed with temporary databases and local servers:

- FastAPI /health and Streamlit /_stcore/health.
- Standalone publisher sent one packet through HTTP to /telemetry.
- HTTP chat requests succeeded for text_only, current_vitals and full_context.
- Dashboard data endpoint returned the newly published current reading.
- `pip check`: no broken requirements.

Temporary servers were stopped after validation. Streamlit interactions were
validated with AppTest and a mocked API; a full interactive browser session was
not tested. No external LLM calls were made. The real agent and RAG are not part
of this branch and have not been validated. Phrase-based safety routing is not
clinically validated. The contract requires joint agreement before integration.

The live smoke test is now checked in as `tests/platform/test_live.py` and runs
with the regular suite. GitHub Actions is configured for Python 3.11 and 3.13;
remote CI results remain unverified until the branches can be pushed.
