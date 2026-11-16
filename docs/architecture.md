# Platform architecture

Streamlit → FastAPI → SQLite supplies synthetic dashboard data independently of
chat context. The standalone simulator posts every five seconds. Startup applies
versioned migrations and creates missing demo profiles with seven days of hourly
samples and sleep records. Existing profiles are never silently reseeded.

Chat validation → profile/consent checks → pre-agent safety route → restricted
context provider → configured agent → validated response. Urgent disclosures
bypass the ordinary agent and return fixed human-support guidance. Statistics
are computed in Python. The platform never infers a mental-health condition from
vitals. Developer 2 owns LangGraph, retrieval, exercises, and answer grounding.

Safety is English phrase matching and deliberately conservative about quoted or
negated emergency phrases. It can miss paraphrases, languages and obfuscated
text; it is not a clinical assessment or a production safety system. Guidance
points to local emergency services for immediate danger and human support.
Reference: https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/
No automated emergency contact is attempted. Model output schema validation is
implemented; clinical/content verification remains an integration concern.

This is a local demo without authentication, authorization between real users,
production retention policies, or deployment hardening. Bind to localhost. All
profiles and measurements are synthetic; mood notes are user-entered local data.
SQLite connections use foreign keys, transactions, parameterized SQL, and close
on every operation. Migrations run under a write lock and roll back on failure.
