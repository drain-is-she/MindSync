from pathlib import Path
from .database import connect

def migrate(path):
    with connect(path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("BEGIN IMMEDIATE")
        for script in sorted(Path(__file__).with_name("migrations").glob("*.sql")):
            if conn.execute("SELECT 1 FROM schema_migrations WHERE version=?", (script.stem,)).fetchone():
                continue
            for statement in script.read_text().split(";"):
                if statement.strip():
                    conn.execute(statement)
            conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (script.stem,))
