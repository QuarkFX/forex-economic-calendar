import os
import sys
import time
from datetime import datetime

# Ensure scripts directory is on sys.path for direct module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scraper import run_all_scrapers

INTERVAL_SECONDS = 900  # 15 minutes (Sweet Spot for economic calendar)

def main():
    print("=" * 60)
    print("QuarkFX Forex Economic Calendar - Cron Runner (Every 15 Minutes)")
    print("Sources: Forex Factory & Myfxbook")
    print("Interval: 15 minutes (900 seconds)")
    print("=" * 60)

    iteration = 1
    while True:
        start_time = time.time()
        print(f"\n>>> Running Cron Job #{iteration} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            run_all_scrapers()
            print(f">>> Cron Job #{iteration} completed successfully.")
        except Exception as e:
            print(f">>> [Error in Job #{iteration}]: {e}")

        elapsed = time.time() - start_time
        sleep_seconds = max(0, INTERVAL_SECONDS - elapsed)
        next_run = datetime.fromtimestamp(time.time() + sleep_seconds).strftime('%Y-%m-%d %H:%M:%S')
        print(f"\nNext run in ~{int(sleep_seconds // 60)} minutes (at {next_run})...")
        iteration += 1
        time.sleep(sleep_seconds)

if __name__ == "__main__":
    main()
