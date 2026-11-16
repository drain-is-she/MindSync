import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    db_path: Path = Path("runtime/mindsync.db")
    agent: str = "mock"
    seed_demo: bool = True
    stale_after_minutes: int = 120
    agent_timeout_seconds: float = 30

    @classmethod
    def from_env(cls):
        return cls(db_path=Path(os.getenv("MINDSYNC_DB_PATH", "runtime/mindsync.db")),
                   agent=os.getenv("MINDSYNC_AGENT", "mock"),
                   seed_demo=os.getenv("MINDSYNC_SEED_DEMO", "true").lower() == "true")
