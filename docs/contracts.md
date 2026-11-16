# Shared contract v1

`src/mindsync/contracts.py` is the source of truth for Developer 2 imports.
The upstream repository was empty at implementation time. This foundation is
proposed on the platform feature branch; it has not been published or merged to
main. Both developers should agree and merge the foundation before building
against it. Treat its fields as frozen after agreement.

Agent entry point:

```python
async def run_agent(request: ChatRequest, context_provider: ContextProvider) -> AgentOutput:
    ...
```

Select the adapter with `MINDSYNC_AGENT=mock|real`. Real mode imports
`mindsync.ai.agent.run_agent` and fails explicitly when it is unavailable.
No fallback disguises a missing real agent. The adapter must be asynchronous,
respect request mode and consent, and handle unavailable readings. Sources and
tool traces must describe actual retrieval/execution; the mock supplies no citations.

| Mode | Current vitals | History | Consent required |
|---|---|---|---|
| text_only | denied | denied | no |
| current_vitals | allowed | denied | yes |
| full_context | allowed | allowed | yes |

The request-scoped provider raises PermissionError for disallowed context or
another profile. This is an application capability boundary, not a sandbox for
untrusted Python. Agents must not open the database directly. Agent session memory
must be partitioned by profile, mode, and consent, including when a caller reuses
session IDs. The platform itself stores no chat memory. Frontend sessions are
partitioned accordingly; each comparison uses three new session IDs.

All vital timestamps require an offset and are normalized to UTC in storage.
Optional vital fields default to null. Numeric values must be finite and in the
schema ranges; these are input plausibility limits, not diagnostic thresholds.
Activity is a normalized 0–1 value. Only simulated telemetry is accepted.
Identical profile/timestamp packets are idempotent; the first write is retained.
Future timestamps are rejected. Missing fields remain null, never zero-filled.

Current readings older than 120 minutes return null. History covers the rolling
seven-day interval, with a mean over non-null heart-rate values. Missing fraction
is the missing share of four fields across expected hourly bins; repeated readings
in a bin cannot mask absent hours. Sleep uses the last seven completed UTC dates,
with the final three dates compared against the earlier four. No empty mean is
invented. `data_stale` means no fresh valid current reading is available.

API: GET /health, GET /profiles, GET /profiles/{id}/vitals, POST /telemetry,
POST /chat. Additionally, GET/POST /profiles/{id}/check-ins supports dashboard mood
entries (integer 1–5, optional note up to 2000 characters). Unknown profiles return
404; invalid input 422; missing context consent 403; agent failure 502; timeout 504.
OpenAPI documentation is available at /docs.
