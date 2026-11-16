# Completion validation

Validated locally on Python 3.13.11:

- 57 tests passed, including real-agent integration, Streamlit AppTest and live HTTP servers.
- 15/15 offline prompt/mode evaluation cases passed.
- `pip check` reported no broken requirements.
- Wheel built successfully; the installed wheel also passed 15/15 evaluation cases outside the checkout.
- `git diff --check` passed.

GitHub Actions runs the full suite and evaluation on Python 3.11 and 3.13.
The agent runs without provider credentials. No external LLM behavior, clinical
outcome, production authentication, or hosted deployment is claimed by these checks.
