> Historical platform-stage document. The local agent is now integrated; see
> [the README](../README.md) and [agent design](agent.md) for current behavior.

# Developer 1 handoff

## Completed chunks

| Chunk | Delivered | Verification |
| --- | --- | --- |
| Foundation | Shared models, context protocol, configuration, packaging | Import and validation tests; separate foundation branch |
| Storage | Versioned SQLite migrations, foreign keys, UTC timestamps, indexes | Fresh/repeated migration, rollback/retry and seed tests |
| Synthetic data | Three profiles, seven-day history, standalone publisher | Determinism, HTTP publishing and failure-path tests |
| Context | Freshness, missingness, pulse and sleep statistics | Exact fixtures, empty histories and dense-sample gap checks |
| Chat | Consent, scoped context, memory-key isolation, safety route, mock adapter | Capabilities, cross-profile denial, urgent bypass and adapter failures |
| Dashboard | Trends, mood, chat, A/B/C, sources and traces | AppTest with mocked and real API responses |
| Delivery | Python matrix CI, live smoke test, wheel verification | 43 local tests and out-of-checkout wheel smoke check |

## Agent integration

Developer 2 owns AI, RAG, exercises and evaluation. No files in those directories
were created or changed. Their async entry point remains:

```python
async def run_agent(request: ChatRequest, context_provider: ContextProvider) -> AgentOutput:
    ...
```

Use `request.session_id` as the agent-memory namespace. The backend replaces the
caller-supplied value with a deterministic key scoped by session, profile, mode
and consent. Repeated requests in the same scope retain continuity. Do not use a
single global conversation history, access SQLite directly, or persist context
outside that namespace. The context provider is a permission boundary for
cooperating application code, not a sandbox for untrusted Python.

Current data can be null when stale or missing. Restricted provider methods raise
PermissionError. History means can be null. Return actual source references and
actual tool execution events; the mock intentionally returns no citations.

The telemetry endpoint's first-write-wins policy returns the stored packet on a
conflicting retry. This does not change the shared schema.

## Review order

1. Review `feat/shared-foundation` against `main` and agree on the shared contract.
2. Merge the foundation through a reviewed pull request.
3. Developer 2 updates their branch from main.
4. Review and merge `feat/platform-iot-ui` through a separate pull request.
5. Integrate Developer 2's implementation; set `MINDSYNC_AGENT=real` explicitly.
6. Run real-agent integration tests with deterministic mocked model/retrieval
   adapters first, checking citations, memory isolation, tool failures, and mode
   restrictions. Live provider testing needs the selected provider configuration.

## Remaining external work and limits

- GitHub returned 403 for authenticated account `drain-is-she`; a repository owner
  must grant write access or the environment must authenticate a permitted account.
  No branch was published and no pull request or remote CI run exists yet.
- Python 3.11 is configured in CI but is not installed locally. Local checks used
  Python 3.13.11; a passing Python 3.11 run remains required before claiming it.
- Real agent/RAG implementation and integration are pending Developer 2.
- Safety matching remains a conservative English prototype, not a clinical
  classifier. Generated answers receive schema validation, not clinical approval.
- This is a localhost demo, without real-user authentication or production hosting.
- Dashboard interaction tests use Streamlit AppTest, not a full browser.

No automatic contact, diagnostic inference, external LLM calls in tests, or
changes to Developer 2's ownership were introduced.
