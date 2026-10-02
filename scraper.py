import os
import json
from datetime import datetime
from forex_factory_scraper import ForexFactoryScraper
from myfxbook_scraper import MyfxbookScraper

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

def save_json(data, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "source_file": filename,
            "updated_at": datetime.now().isoformat(),
            "count": len(data),
            "events": data
        }, f, indent=2, ensure_ascii=False)
    print(f"[Scraper] Saved {len(data)} events to {filepath}")
    return filepath

def run_all_scrapers():
    print(f"\n==========================================")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Scraping Cycle...")
    print(f"==========================================")
    
    # 1. Forex Factory
    print("\n[1/4] Scraping Forex Factory - This Week...")
    ff = ForexFactoryScraper()
    ff_thisweek = ff.get_this_week()
    save_json(ff_thisweek, "forexfactory_thisweek.json")

    print("\n[2/4] Scraping Forex Factory - 21 Days (3 Weeks)...")
    ff_21days = ff.get_21_days()
    save_json(ff_21days, "forexfactory_21days.json")

    # 2. Myfxbook
    print("\n[3/4] Scraping Myfxbook - This Week...")
    mfb = MyfxbookScraper()
    mfb_thisweek = mfb.get_this_week()
    save_json(mfb_thisweek, "myfxbook_thisweek.json")

    print("\n[4/4] Scraping Myfxbook - 21 Days (3 Weeks)...")
    mfb_21days = mfb.get_21_days()
    save_json(mfb_21days, "myfxbook_21days.json")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scraping Completed Successfully!\n")

if __name__ == "__main__":
    run_all_scrapers()
