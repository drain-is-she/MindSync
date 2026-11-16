CREATE TABLE profiles (id TEXT PRIMARY KEY, name TEXT NOT NULL, scenario TEXT NOT NULL);
CREATE TABLE vital_samples (
 id INTEGER PRIMARY KEY, profile_id TEXT NOT NULL REFERENCES profiles(id),
 measured_at TEXT NOT NULL, heart_rate_bpm REAL CHECK(heart_rate_bpm BETWEEN 20 AND 250),
 spo2_percent REAL CHECK(spo2_percent BETWEEN 50 AND 100),
 respiratory_rate_per_min REAL CHECK(respiratory_rate_per_min BETWEEN 3 AND 80),
 activity_level REAL CHECK(activity_level BETWEEN 0 AND 1),
 simulated INTEGER NOT NULL DEFAULT 1 CHECK(simulated=1), UNIQUE(profile_id, measured_at));
CREATE INDEX vitals_profile_time ON vital_samples(profile_id, measured_at);
CREATE TABLE daily_sleep (profile_id TEXT NOT NULL REFERENCES profiles(id), sleep_date TEXT NOT NULL,
 hours REAL CHECK(hours BETWEEN 0 AND 24), PRIMARY KEY(profile_id, sleep_date));
CREATE TABLE check_ins (id INTEGER PRIMARY KEY, profile_id TEXT NOT NULL REFERENCES profiles(id),
 recorded_at TEXT NOT NULL, mood INTEGER NOT NULL CHECK(mood BETWEEN 1 AND 5), note TEXT NOT NULL DEFAULT '');
CREATE INDEX check_ins_profile_time ON check_ins(profile_id, recorded_at);
