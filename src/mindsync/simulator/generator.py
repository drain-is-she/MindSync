import math
import random
from mindsync.contracts import VitalReading

PROFILES = [
    ("student_a", "Student A", "Exam week with gradually reduced sleep"),
    ("student_b", "Student B", "Afternoon physical activity and pulse variation"),
    ("student_c", "Student C", "Missing, stale and noisy synthetic sensor samples"),
]

def generate(profile_id, measured_at, rng=None):
    rng = rng or random.Random(42)
    hour = measured_at.hour + measured_at.minute / 60
    active = 0.8 if profile_id == "student_b" and 16 <= hour < 18 else 0.15
    hr = 68 + 8 * math.sin((hour - 8) * math.pi / 12) + active * 40
    if profile_id == "student_a":
        hr += 6
    hr += rng.gauss(0, 9 if profile_id == "student_c" else 2)
    return VitalReading(profile_id=profile_id, measured_at=measured_at,
        heart_rate_bpm=round(max(40, min(180, hr)), 1),
        spo2_percent=None if profile_id == "student_c" and rng.random() < .4 else round(rng.uniform(96, 99), 1),
        respiratory_rate_per_min=round(14 + active * 8 + rng.random(), 1), activity_level=active)
