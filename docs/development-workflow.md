# MindSync development workflow

This repository is prepared for two developers. Application implementation has not started.

## Branches

| Branch | Purpose |
| --- | --- |
| `main` | Shared integration branch |
| `codex/dev1-platform` | Developer 1: platform, storage, simulator and frontend |
| `feat/langgraph-rag-eval` | Developer 2: intelligence, RAG, activities and evaluation |

Both developer branches start from the same repository setup commit. After initialization, integrate changes into `main` through reviewed pull requests. Do not force-push shared branches.

## Ownership

| Owner | Paths |
| --- | --- |
| Developer 1 | `src/mindsync/contracts.py`, `src/mindsync/config.py`, `src/mindsync/__init__.py`, `src/mindsync/platform/`, `src/mindsync/storage/`, `src/mindsync/simulator/`, `frontend/`, `tests/platform/` |
| Developer 1 | `pyproject.toml`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`; shared foundation and packaging |
| Developer 2 | `src/mindsync/ai/`, `src/mindsync/rag/`, `src/mindsync/activities/`, `data/knowledge/`, `evaluation/`, `tests/ai/`, `docs/dependency-requests.md` |
| Coordinated integration | `tests/integration/`, `docs/architecture.md`, `docs/contracts.md` and changes to the agreed public interface |

Keep changes inside your owned paths. Record new dependency requests in `docs/dependency-requests.md`; Developer 1 updates the shared dependency files. Coordinate shared changes before editing them.

## Foundation comes first

Developer 1 creates the Python 3.11 package foundation and freezes the Pydantic v2 contracts in a foundation pull request. The foundation is not present yet. Developer 2 imports those committed contracts rather than creating substitutes. Once the foundation is merged, both developers update their branches from `main`.

The intended interface is `async def run_agent(request: ChatRequest, context_provider: ContextProvider) -> AgentOutput`. The actual definitions in `mindsync.contracts` are authoritative. Developer 1 owns the safety gate and urgent-support routing. Developer 2 accesses physiology only through `ContextProvider` and tests with deterministic fake providers.

## Local checkouts

Use a separate checkout for each developer.

Developer 1:

```bash
git clone --branch codex/dev1-platform https://github.com/Vansh-A1/MindSync.git mindsync-dev1
cd mindsync-dev1
```

Developer 2:

```bash
git clone --branch feat/langgraph-rag-eval https://github.com/Vansh-A1/MindSync.git mindsync-dev2
cd mindsync-dev2
```

After committing or safely setting aside local work, incorporate shared updates with `git fetch origin` followed by `git merge origin/main`. Open each implementation pull request from the developer branch into `main`, describing changes, relevant verification and integration dependencies.

## Configuration and generated files

Use a free-tier model API for live operation and mocked model behavior for automated tests. Developer 1 owns centralized configuration. Use the same model and general instructions across text-only, current-vitals and full-context comparisons.

Never commit API keys, secret environment files, private conversations, model weights, virtual environments or generated indexes. The foundation must ignore `runtime/`, environments and local caches. Generated RAG indexes belong under `runtime/rag_index`.

## Setup scope

This setup supplies a common starting commit and two development branches. It does not supply application code, frozen contracts, CI checks, collaborator invitations or enforced branch-protection rules. The pull-request and ownership rules above are documented conventions until repository enforcement is configured.
