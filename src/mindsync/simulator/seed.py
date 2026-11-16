import random
from datetime import datetime, timedelta, timezone
from mindsync.storage.database import connect
from mindsync.storage.repository import insert_vital
from .generator import PROFILES, generate

def seed(path, now=None, seed_value=42):
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    rng = random.Random(seed_value)
    with connect(path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        for profile_id, name, scenario in PROFILES:
            # Existing profiles are never reseeded, including intentionally empty ones.
            if conn.execute("SELECT 1 FROM profiles WHERE id=?", (profile_id,)).fetchone():
                continue
            conn.execute("INSERT INTO profiles VALUES (?,?,?)", (profile_id, name, scenario))
            for offset in range(167, -1, -1):
                if profile_id == "student_c" and (offset < 12 or rng.random() < .25):
                    continue
                insert_vital(conn, generate(profile_id, now - timedelta(hours=offset), rng))
            for day in range(7, 0, -1):
                hours = (5 + day * .4 if profile_id == "student_a" else 7.5) + rng.uniform(-.3, .3)
                if profile_id == "student_c" and day in (2, 5):
                    hours = None
                conn.execute("INSERT INTO daily_sleep VALUES (?,?,?)", (profile_id, (now-timedelta(days=day)).date().isoformat(), hours))

if __name__ == "__main__":
    from mindsync.config import Settings
    from mindsync.storage.migrations import migrate
    path = Settings.from_env().db_path
    migrate(path)
    seed(path)
    print(f"Demo data ready in {path}")
