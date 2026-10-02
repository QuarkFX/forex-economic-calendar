import time
import sys
from datetime import datetime
from scraper import run_all_scrapers

INTERVAL_SECONDS = 300  # 5 minutes

def main():
    print("=" * 60)
    print("QuarkFX Forex Economic Calendar - Cron Runner (Every 5 Minutes)")
    print("Sources: Forex Factory & Myfxbook")
    print("Interval: 5 minutes (300 seconds)")
    print("=" * 60)

    iteration = 1
    while True:
        print(f"\n>>> Running Cron Job #{iteration} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            run_all_scrapers()
            print(f">>> Cron Job #{iteration} completed successfully.")
        except Exception as e:
            print(f">>> [Error in Job #{iteration}]: {e}")

        print(f"\nNext run in 5 minutes (at {(datetime.now().timestamp() + INTERVAL_SECONDS)})...")
        iteration += 1
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
