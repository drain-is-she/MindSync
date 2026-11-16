# Integrated agent

`mindsync.ai.agent.run_agent` implements the shared async contract without changing
API request or response schemas. LangGraph orchestrates three nodes: permission-
appropriate context collection, ranked lexical retrieval, and deterministic
composition. Fresh measurements and summaries are descriptive only. They never
select an exercise or imply a diagnosis.

The knowledge base contains original short paraphrases of three NHS pages,
verified on 2026-11-16:

- [Sleep routine and relaxation](https://www.nhs.uk/every-mind-matters/mental-wellbeing-tips/how-to-fall-asleep-faster-and-sleep-better/)
- [Worry time and making a plan](https://www.nhs.uk/every-mind-matters/mental-wellbeing-tips/self-help-cbt-techniques/tackling-your-worries/)
- [Gentle breathing](https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/breathing-exercises-for-stress/)

Retrieval matches whole words against topic vocabularies and returns the highest
scoring chunk, with stable ordering for ties. An unmatched query returns no
citations and asks the user to choose a supported topic. Follow-up terms can reuse
the prior topic within the same scope. Source identifiers in replies refer to the
returned SourceRef; instructions and citations cannot be supplied by user text.
There is no model, external tracing configuration, vector database, page scraping,
or user-document ingestion in this implementation.

Context errors produce actual error tool events and do not suppress text support.
No missing reading is fabricated. The existing HTTP timeout and response schema
checks remain in force. Urgent messages bypass both retrieval and context; direct
agent calls also enforce urgency and consent. Phrase-based safety and lexical
retrieval are intentionally limited and are not clinical systems.

Only topic labels are cached, with a 30-minute expiry and a 256-scope cap protected
by a lock. Request keys include session, profile, mode and consent, in addition to
the platform's hashed namespace. No LangGraph persistent checkpointer stores
messages or measurements. Concurrent requests in the same scope use the last
completed topic update. Multiple processes do not share topic state.

Run `python -m mindsync.evaluation` for 15 reproducible API checks across supported,
unsupported, and urgent prompts in all three modes. Unit and integration tests add
permission, failures, expiry, source, dashboard, and live server coverage. These
checks establish software behavior, not clinical quality or broad language ability.
