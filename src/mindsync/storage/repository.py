from datetime import datetime, timezone
from .database import connect
from mindsync.contracts import VitalReading

def utc_string(value):
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")

class Repository:
    def __init__(self, path):
        self.path = path

    def profiles(self):
        with connect(self.path) as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM profiles ORDER BY id")]

    def exists(self, profile_id):
        with connect(self.path) as conn:
            return conn.execute("SELECT 1 FROM profiles WHERE id=?", (profile_id,)).fetchone() is not None

    def save_vital(self, reading: VitalReading):
        with connect(self.path) as conn:
            insert_vital(conn, reading)

    def samples(self, profile_id, start, end):
        with connect(self.path) as conn:
            rows = conn.execute("SELECT * FROM vital_samples WHERE profile_id=? AND measured_at>=? AND measured_at<=? ORDER BY measured_at", (profile_id, utc_string(start), utc_string(end))).fetchall()
        return [VitalReading(**{k: row[k] for k in VitalReading.model_fields}) for row in rows]

    def latest(self, profile_id, now):
        with connect(self.path) as conn:
            row = conn.execute("SELECT * FROM vital_samples WHERE profile_id=? AND measured_at<=? AND (heart_rate_bpm IS NOT NULL OR spo2_percent IS NOT NULL OR respiratory_rate_per_min IS NOT NULL OR activity_level IS NOT NULL) ORDER BY measured_at DESC LIMIT 1", (profile_id, utc_string(now))).fetchone()
        return VitalReading(**{k: row[k] for k in VitalReading.model_fields}) if row else None

    def sleep(self, profile_id, start, end):
        with connect(self.path) as conn:
            return [dict(row) for row in conn.execute("SELECT sleep_date, hours FROM daily_sleep WHERE profile_id=? AND sleep_date>=? AND sleep_date<? ORDER BY sleep_date", (profile_id, start.isoformat(), end.isoformat()))]

    def check_in(self, profile_id, mood, note):
        with connect(self.path) as conn:
            conn.execute("INSERT INTO check_ins(profile_id,recorded_at,mood,note) VALUES (?,?,?,?)", (profile_id, utc_string(datetime.now(timezone.utc)), mood, note))

    def check_ins(self, profile_id):
        with connect(self.path) as conn:
            return [dict(row) for row in conn.execute("SELECT recorded_at,mood,note FROM check_ins WHERE profile_id=? ORDER BY recorded_at DESC LIMIT 100", (profile_id,))]

def insert_vital(conn, reading):
    conn.execute("INSERT INTO vital_samples(profile_id,measured_at,heart_rate_bpm,spo2_percent,respiratory_rate_per_min,activity_level,simulated) VALUES (?,?,?,?,?,?,1) ON CONFLICT(profile_id,measured_at) DO NOTHING", (reading.profile_id, utc_string(reading.measured_at), reading.heart_rate_bpm, reading.spo2_percent, reading.respiratory_rate_per_min, reading.activity_level))
