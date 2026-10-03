import os
import json
import time
import hashlib
from datetime import datetime, timezone
from forex_factory_scraper import ForexFactoryScraper
from myfxbook_scraper import MyfxbookScraper

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

def _compute_events_hash(events):
    """Compute deterministic SHA-256 hash of events payload to detect actual content changes."""
    payload = json.dumps(events or [], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def save_json(data, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    existing_events = []
    existing_hash = None

    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_events = existing_data.get("events", [])
                existing_hash = _compute_events_hash(existing_events)
        except Exception as e:
            print(f"[Scraper] Warning reading existing {filename}: {e}")

    # Fail-safe 1: Never overwrite valid existing data with an empty list
    if (not data or len(data) == 0) and existing_events:
        print(f"[Scraper] Warning: Scraped data for {filename} is empty. Retaining previous valid file.")
        return filepath

    # Fail-safe 2: Prevent partial wipeout on 21-day datasets if sub-queries failed
    if filename.endswith("21days.json") and existing_events:
        if len(data) < len(existing_events) * 0.5:
            print(f"[Scraper] Warning: Incomplete 21-day dataset for {filename} ({len(data)} events vs {len(existing_events)} previous). Retaining previous valid file.")
            return filepath

    # Smart Change Detection: Avoid useless git commits if payload has not changed
    new_hash = _compute_events_hash(data)
    if existing_hash and new_hash == existing_hash:
        print(f"[Scraper] No content changes for {filename} ({len(data)} events). Keeping existing file.")
        return filepath

    tmp_filepath = filepath + ".tmp"
    with open(tmp_filepath, "w", encoding="utf-8") as f:
        json.dump({
            "source_file": filename,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "count": len(data) if data else 0,
            "events": data or []
        }, f, indent=2, ensure_ascii=False)
    
    # Atomic replace with retry to prevent Windows file locking collisions
    for attempt in range(3):
        try:
            os.replace(tmp_filepath, filepath)
            break
        except PermissionError:
            if attempt < 2:
                time.sleep(0.1)
            else:
                try:
                    os.remove(filepath)
                    os.replace(tmp_filepath, filepath)
                except Exception:
                    pass
    print(f"[Scraper] Saved updated data ({len(data) if data else 0} events) to {filepath}")
    return filepath

def run_all_scrapers():
    print(f"\n==========================================")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Scraping Cycle...")
    print(f"==========================================")
    
    # 1. Forex Factory
    print("\n[1/4] Scraping Forex Factory - This Week...")
    ff = ForexFactoryScraper()
    try:
        ff_thisweek = ff.get_this_week()
        save_json(ff_thisweek, "forexfactory_thisweek.json")

        print("\n[2/4] Scraping Forex Factory - 21 Days (3 Weeks)...")
        ff_21days = ff.get_21_days()
        save_json(ff_21days, "forexfactory_21days.json")
    except Exception as e:
        print(f"[Scraper] Forex Factory scraping error: {e}")
    finally:
        ff.close()

    # 2. Myfxbook
    print("\n[3/4] Scraping Myfxbook - This Week...")
    mfb = MyfxbookScraper()
    try:
        mfb_thisweek = mfb.get_this_week()
        save_json(mfb_thisweek, "myfxbook_thisweek.json")

        print("\n[4/4] Scraping Myfxbook - 21 Days (3 Weeks)...")
        mfb_21days = mfb.get_21_days()
        save_json(mfb_21days, "myfxbook_21days.json")
    except Exception as e:
        print(f"[Scraper] Myfxbook scraping error: {e}")
    finally:
        mfb.close()

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scraping Completed Successfully!\n")

if __name__ == "__main__":
    run_all_scrapers()
