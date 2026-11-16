import argparse
import random
import time
from datetime import datetime, timezone
import httpx
from .generator import generate

def main():
    parser = argparse.ArgumentParser(description="Publish synthetic telemetry every five seconds")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--profile", choices=["student_a", "student_b", "student_c"], default="student_a")
    parser.add_argument("--count", type=int, default=0, help="0 publishes until Ctrl-C")
    args = parser.parse_args()
    if args.count < 0:
        parser.error("--count must be zero or a positive integer")
    rng = random.Random(42)
    failed = False
    try:
        with httpx.Client(timeout=5) as client:
            count = 0
            while args.count == 0 or count < args.count:
                will_retry = args.count == 0 or count + 1 < args.count
                packet = generate(args.profile, datetime.now(timezone.utc), rng)
                try:
                    response = client.post(args.url.rstrip("/")+"/telemetry", json=packet.model_dump(mode="json"))
                    response.raise_for_status()
                    print(f"Published simulated reading for {args.profile}", flush=True)
                except httpx.HTTPError as exc:
                    failed = True
                    suffix = " Next attempt in five seconds." if will_retry else " No attempts remain."
                    print(f"Telemetry unavailable: {exc}.{suffix}", flush=True)
                count += 1
                if will_retry:
                    time.sleep(5)
    except KeyboardInterrupt:
        print("Simulator stopped.")
        return 130
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
