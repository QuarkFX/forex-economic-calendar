import os
import sys
import re
import json
import time
import hashlib
from datetime import datetime, timezone
from curl_cffi import requests
from bs4 import BeautifulSoup

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT_DIR, ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _parse_mfb_datetime(raw_date, raw_time):
    """Parse Myfxbook date and time into standardized UTC ISO 8601 and epoch timestamp."""
    f_date, f_time, iso_dt, epoch_ts = raw_date, raw_time, None, None
    try:
        date_clean = (raw_date or "").strip()
        date_obj = None
        for dfmt in ("%A, %b %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
            try:
                date_obj = datetime.strptime(date_clean, dfmt)
                break
            except Exception:
                continue

        if date_obj:
            f_date = date_obj.strftime("%Y-%m-%d")
            tm = re.search(r"(\d{1,2}):(\d{2})", raw_time or "")
            if tm:
                hr, mn = int(tm.group(1)), int(tm.group(2))
                f_time = f"{hr:02d}:{mn:02d}"
                dt = datetime(date_obj.year, date_obj.month, date_obj.day, hr, mn, tzinfo=timezone.utc)
            else:
                f_time = raw_time or "All Day"
                dt = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, tzinfo=timezone.utc)
            iso_dt = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            epoch_ts = int(dt.timestamp())
    except Exception:
        pass
    return f_date, f_time, iso_dt, epoch_ts

def _dedup_mfb_events(*lists):
    """Merge and deduplicate Myfxbook events by composite key and ensure strict chronological order."""
    merged, seen = [], set()
    for elist in lists:
        for ev in (elist or []):
            key = ev.get("id") or (ev.get("date"), ev.get("time"), ev.get("country"), ev.get("title"))
            if key not in seen:
                seen.add(key)
                merged.append(ev)
    merged.sort(key=lambda x: (x.get("timestamp") or 0, x.get("title", "")))
    return merged

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

class MyfxbookScraper:
    def __init__(self):
        self.base_url = "https://www.myfxbook.com/forex-economic-calendar"
        self.impersonate = "chrome124"
        self.session = requests.Session()
        self._warmed = False
        self.driver = None
        self.display = None

    def _get_driver(self):
        """Lazy-initialize SeleniumBase UC Mode driver with virtual display on Linux."""
        if self.driver is not None:
            return self.driver

        print("[Myfxbook] Initializing SeleniumBase UC Mode driver...")
        try:
            from seleniumbase import Driver

            is_linux = sys.platform.startswith("linux")
            if is_linux:
                try:
                    from sbvirtualdisplay import Display
                    self.display = Display(visible=False, size=(1440, 900))
                    self.display.start()
                    print("[Myfxbook] Virtual display (Xvfb) initialized successfully.")
                except Exception as de:
                    print(f"[Myfxbook] Virtual display notice: {de}")
                    self.display = None

            # On Linux with Xvfb, run headed to eliminate headless anti-bot signatures.
            # On Windows/macOS, headless=True operates cleanly.
            use_headless = False if (is_linux and self.display is not None) else True
            self.driver = Driver(uc=True, headless=use_headless)
            return self.driver
        except Exception as e:
            print(f"[Myfxbook] Driver initialization failed: {e}")
            self.driver = None
            return None

    def close(self):
        """Close browser driver, virtual display, and HTTP session to prevent leaks."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

        if self.display:
            try:
                self.display.stop()
            except Exception:
                pass
            self.display = None

        try:
            self.session.close()
        except Exception:
            pass

    def _warm_session(self):
        """Warm curl_cffi session by visiting homepage first."""
        if self._warmed:
            return
        try:
            self.session.get("https://www.myfxbook.com/", impersonate=self.impersonate, headers=DEFAULT_HEADERS, timeout=15)
            self._warmed = True
            time.sleep(1)
        except Exception as e:
            print(f"[Myfxbook] Session warming notice: {e}")

    def _read_cache(self, key, max_age):
        path = os.path.join(CACHE_DIR, f"mfb_{key}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                    if time.time() - entry.get("timestamp", 0) < max_age:
                        return entry.get("data")
            except Exception:
                pass
        return None

    def _write_cache(self, key, data):
        try:
            with open(os.path.join(CACHE_DIR, f"mfb_{key}.json"), "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "data": data}, f)
        except Exception:
            pass

    def _parse_html(self, html_text):
        """Extract structured events from Myfxbook economic calendar HTML."""
        if not html_text:
            return []

        soup = BeautifulSoup(html_text, "html.parser")
        table = soup.find("table", {"id": "economicCalendarTable"})
        if not table:
            return []

        events, cur_date = [], ""
        for tr in table.find_all("tr"):
            classes = tr.get("class", [])
            if "economicCalendarDateRow" in classes:
                cur_date = tr.text.strip()
            elif "economicCalendarRow" in classes:
                tds = tr.find_all("td")
                if len(tds) >= 9:
                    raw_time = tds[0].text.strip()
                    currency = tds[3].text.strip()
                    title = " ".join(tds[4].text.strip().replace("\n", " ").split())
                    impact_val = tds[5].text.strip()
                    if not impact_val or impact_val.lower() in ["none", "holiday", "non-economic"]:
                        impact = "Non-Economic"
                    else:
                        impact = impact_val.capitalize()
                    prev_val = tds[6].text.strip()
                    cons_val = tds[7].text.strip()
                    act_val = tds[8].text.strip()

                    act_classes = " ".join(tds[8].get("class", [])).lower()
                    actual_state = "neutral"
                    if "background-transparent-green" in act_classes:
                        actual_state = "better"
                    elif "background-transparent-red" in act_classes:
                        actual_state = "worse"

                    f_date, f_time, iso_dt, ts = _parse_mfb_datetime(cur_date, raw_time)

                    raw_id = tr.get("data-row-id", "").strip() or tr.get("id", "").replace("calRow", "").strip()
                    if raw_id:
                        event_id = f"mfb_{raw_id}"
                    elif ts:
                        event_id = f"mfb_{ts}_{currency}"
                    else:
                        fallback_h = hashlib.md5(f"{title}_{f_date}_{f_time}_{currency}".encode('utf-8')).hexdigest()[:10]
                        event_id = f"mfb_{fallback_h}"

                    events.append({
                        "id": event_id,
                        "title": title,
                        "country": currency,
                        "datetime": iso_dt,
                        "timestamp": ts,
                        "date": f_date,
                        "time": f_time,
                        "timezone": "UTC",
                        "impact": impact,
                        "forecast": cons_val,
                        "consensus": cons_val,
                        "previous": prev_val,
                        "actual": act_val,
                        "actual_state": actual_state,
                        "raw_date": cur_date
                    })
        return events

    def _fetch_html_uc(self, period_id, max_retries=2):
        """Fetch economic calendar HTML using SeleniumBase UC Mode."""
        driver = self._get_driver()
        if not driver:
            return None

        url = f"{self.base_url}?calPeriod={period_id}"
        for attempt in range(1, max_retries + 1):
            try:
                driver.uc_open_with_reconnect(url, reconnect_time=3)
                
                # Check for Cloudflare challenge screens and settle
                for _ in range(8):
                    title = driver.title or ""
                    if any(chal in title for chal in ["Attention Required", "Just a moment", "Cloudflare"]):
                        time.sleep(2)
                        try:
                            driver.uc_gui_click_captcha()
                        except Exception:
                            pass
                    else:
                        break

                page_source = driver.page_source or ""
                if "economicCalendarTable" in page_source:
                    return page_source
                else:
                    title = driver.title or "Unknown"
                    print(f"[Myfxbook UC] Period {period_id} Attempt {attempt}: Table not found. Title: '{title}'")
                    time.sleep(2 * attempt)
            except Exception as e:
                print(f"[Myfxbook UC] Period {period_id} Attempt {attempt} Exception: {e}")
                time.sleep(2)
        return None

    def _scrape_period_curl(self, period_id):
        """Fallback fast scraper using curl_cffi if SeleniumBase driver is unavailable."""
        url = f"{self.base_url}?calPeriod={period_id}"
        period_headers = dict(DEFAULT_HEADERS)
        period_headers["Referer"] = "https://www.myfxbook.com/"
        try:
            self._warm_session()
            r = self.session.get(url, impersonate=self.impersonate, headers=period_headers, timeout=20)
            if r.status_code == 200 and "economicCalendarTable" in r.text:
                return self._parse_html(r.text)
            else:
                title_match = re.search(r'<title>(.*?)</title>', r.text, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else "No Title"
                print(f"[Myfxbook curl_cffi] Period {period_id}: HTTP {r.status_code}. Title: '{title}'")
        except Exception as e:
            print(f"[Myfxbook curl_cffi] Period {period_id} Exception: {e}")
        return []

    def _scrape_period(self, period_id, max_retries=2):
        """Scrape economic calendar for a specific calPeriod with SeleniumBase UC Mode."""
        # 1. Primary engine: SeleniumBase UC Mode
        driver = self._get_driver()
        if driver:
            html = self._fetch_html_uc(period_id, max_retries=max_retries)
            if html:
                events = self._parse_html(html)
                if events:
                    return events

        # 2. Resilient fallback: curl_cffi (if driver failed or returned no events)
        print(f"[Myfxbook] Attempting curl_cffi fallback for period {period_id}...")
        return self._scrape_period_curl(period_id)

    def get_this_week(self, force_refresh=True):
        """Fetch this week's events (calPeriod=3) with live actuals."""
        if not force_refresh:
            cached = self._read_cache("this_week", 300)
            if cached:
                return cached

        fresh = self._scrape_period(3)
        if fresh:
            self._write_cache("this_week", fresh)
            return fresh

        return self._read_cache("this_week", 86400) or []

    def get_21_days(self):
        """Fetch 21 consecutive days (Previous Week + This Week + Next Week) with resilient fallback."""
        # 1. Previous Week (24h cache)
        last_week = self._read_cache("last_week", 86400)
        if not last_week:
            last_week = self._scrape_period(2)
            if last_week:
                self._write_cache("last_week", last_week)
            time.sleep(1)

        # 2. This Week (reuses live data from current cycle, no duplicate request)
        this_week = self.get_this_week(force_refresh=False)

        # 3. Next Week (2h cache)
        next_week = self._read_cache("next_week", 7200)
        if not next_week:
            next_week = self._scrape_period(9)
            if next_week:
                self._write_cache("next_week", next_week)
            time.sleep(1)

        # Resilient fallback: If live scrape failed, reuse last known good cache up to 7 days
        if not last_week:
            last_week = self._read_cache("last_week", 86400 * 7) or []
        if not next_week:
            next_week = self._read_cache("next_week", 86400 * 7) or []

        return _dedup_mfb_events(last_week, this_week, next_week)
