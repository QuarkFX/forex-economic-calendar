import os
import re
import json
import time
import hashlib
from datetime import datetime, timezone, timedelta
from curl_cffi import requests
from bs4 import BeautifulSoup

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

def _parse_ff_datetime(date_str, time_str, base_year, tz_offset_hours=0.0):
    """
    Parse ForexFactory date and time strings into standardized UTC ISO 8601 and epoch timestamp.
    Dynamically converts using the timezone offset embedded by Forex Factory (window.FF.timezone)
    and handles December/January year rollovers.
    """
    f_date, f_time, iso_dt, epoch_ts = date_str, time_str, None, None
    try:
        m = re.search(r'(?:[A-Za-z]{3}\s+)?([A-Za-z]{3})\s+(\d{1,2})', date_str)
        if m:
            mon_str, day_str = m.groups()
            mon_num = MONTH_MAP.get(mon_str.lower(), 1)
            day = int(day_str)

            # Year rollover handling:
            # If current month is Dec and event month is Jan, event belongs to base_year + 1.
            # If current month is Jan and event month is Dec, event belongs to base_year - 1.
            now_month = datetime.now().month
            year = base_year
            if now_month == 12 and mon_num == 1:
                year += 1
            elif now_month == 1 and mon_num == 12:
                year -= 1

            tz = timezone(timedelta(hours=tz_offset_hours))

            tm = re.search(r'(\d{1,2}):(\d{2})(am|pm)?', time_str or '', re.IGNORECASE)
            if tm:
                hr, mn = int(tm.group(1)), int(tm.group(2))
                ampm = tm.group(3)
                if ampm:
                    if ampm.lower() == 'pm' and hr != 12:
                        hr += 12
                    elif ampm.lower() == 'am' and hr == 12:
                        hr = 0
                
                # Attach the scraped page timezone offset and convert to UTC
                dt_local = datetime(year, mon_num, day, hr, mn, tzinfo=tz)
                dt_utc = dt_local.astimezone(timezone.utc)

                f_date = dt_utc.strftime("%Y-%m-%d")
                f_time = dt_utc.strftime("%H:%M")
                iso_dt = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                epoch_ts = int(dt_utc.timestamp())
            else:
                # "All Day", "Tentative", "Day 1", etc.
                # All-day/tentative events belong to the stated calendar date itself.
                # Anchor directly to UTC midnight without applying time zone offsets.
                f_time = (time_str or "").strip() or "All Day"
                dt_utc = datetime(year, mon_num, day, 0, 0, tzinfo=timezone.utc)
                f_date = dt_utc.strftime("%Y-%m-%d")
                iso_dt = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
                epoch_ts = int(dt_utc.timestamp())
    except Exception:
        pass
    return f_date, f_time, iso_dt, epoch_ts

def _dedup_events(*lists):
    """Merge and deduplicate event lists while preserving strict chronological order."""
    merged, seen = [], set()
    for elist in lists:
        for ev in (elist or []):
            key = ev.get("id") or (ev.get("date"), ev.get("time"), ev.get("country"), ev.get("title"))
            if key not in seen:
                seen.add(key)
                merged.append(ev)
    # Ensure all events are strictly sorted chronologically by timestamp
    merged.sort(key=lambda x: (x.get("timestamp") or 0, x.get("title", "")))
    return merged

class ForexFactoryScraper:
    def __init__(self):
        self.base_url = "https://www.forexfactory.com/calendar"
        self.session = requests.Session()

    def close(self):
        """Close HTTP session to prevent socket leaks."""
        try:
            self.session.close()
        except Exception:
            pass

    def _read_cache(self, key, max_age):
        path = os.path.join(CACHE_DIR, f"ff_{key}.json")
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
            with open(os.path.join(CACHE_DIR, f"ff_{key}.json"), "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "data": data}, f)
        except Exception:
            pass

    def get_this_week(self, force_refresh=True):
        """Fetch this week's events with live actual releases (cached/refreshed every 5 min)."""
        if not force_refresh:
            cached = self._read_cache("this_week", 300)
            if cached:
                return cached

        fresh = self._scrape_html_calendar("week=this")
        if fresh:
            self._write_cache("this_week", fresh)
            return fresh

        # Direct cache fallback to protect live actuals
        return self._read_cache("this_week", 86400) or []

    def get_21_days(self):
        """Fetch 21 consecutive days (Previous Week + This Week + Next Week) with resilient fallback."""
        # Previous Week (24h cache)
        last_week = self._read_cache("last_week", 86400)
        if not last_week:
            last_week = self._scrape_html_calendar("week=last")
            if last_week:
                self._write_cache("last_week", last_week)
            time.sleep(1)

        # This Week (reuses live data from current cycle, no duplicate request)
        this_week = self.get_this_week(force_refresh=False)

        # Next Week (2h cache)
        next_week = self._read_cache("next_week", 7200)
        if not next_week:
            next_week = self._scrape_html_calendar("week=next")
            if next_week:
                self._write_cache("next_week", next_week)
            time.sleep(1)

        # Resilient fallback: If live scrape failed, reuse last known good cache up to 7 days
        if not last_week:
            last_week = self._read_cache("last_week", 86400 * 7) or []
        if not next_week:
            next_week = self._read_cache("next_week", 86400 * 7) or []

        return _dedup_events(last_week, this_week, next_week)

    def _scrape_html_calendar(self, query, max_retries=3):
        url = f"{self.base_url}?{query}"
        for attempt in range(1, max_retries + 1):
            try:
                r = self.session.get(url, impersonate="safari15_3", timeout=25)
                if r.status_code == 200:
                    # Extract rendered timezone offset from window.FF configuration
                    tz_offset_hours = 0.0
                    tz_match = re.search(r'timezone:\s*[\'"]([+-]?\d+(?:\.\d+)?)', r.text)
                    if tz_match:
                        try:
                            tz_offset_hours = float(tz_match.group(1).replace('+', ''))
                        except (ValueError, TypeError):
                            tz_offset_hours = 0.0

                    soup = BeautifulSoup(r.text, "html.parser")
                    events, cur_date, cur_time = [], "", ""
                    base_year = datetime.now().year

                    for row in soup.find_all("tr", class_="calendar__row"):
                        if "calendar__row--day-breaker" in row.get("class", []):
                            continue

                        d_cell = row.find("span", class_="date")
                        if d_cell and d_cell.text.strip():
                            cur_date, cur_time = d_cell.text.strip(), ""

                        t_cell = row.find("span", class_="calendar__event-title")
                        if not t_cell:
                            continue

                        tm_cell = row.find("td", class_="calendar__time")
                        if tm_cell and tm_cell.text.strip():
                            cur_time = tm_cell.text.strip()

                        curr_cell = row.find("td", class_="calendar__currency")
                        currency = curr_cell.text.strip() if curr_cell else ""

                        impact_cell = row.find("td", class_="calendar__impact")
                        impact = "Low"
                        if impact_cell:
                            sp = impact_cell.find("span")
                            if sp and "class" in sp.attrs:
                                cls = " ".join(sp["class"]).lower()
                                if "red" in cls or "high" in cls:
                                    impact = "High"
                                elif "ora" in cls or "orange" in cls or "medium" in cls:
                                    impact = "Medium"
                                elif "yel" in cls or "yellow" in cls or "low" in cls:
                                    impact = "Low"
                                elif "gra" in cls or "gray" in cls or "holiday" in cls:
                                    impact = "Non-Economic"

                        fc = row.find("td", class_="calendar__forecast")
                        pv = row.find("td", class_="calendar__previous")
                        ac = row.find("td", class_="calendar__actual")

                        forecast_val = fc.text.strip() if fc else ""
                        actual_val = ac.text.strip() if ac else ""
                        actual_state = "neutral"
                        if ac:
                            sp = ac.find("span")
                            classes = " ".join(sp.get("class", [])).lower() if (sp and "class" in sp.attrs) else " ".join(ac.get("class", [])).lower()
                            if "better" in classes:
                                actual_state = "better"
                            elif "worse" in classes:
                                actual_state = "worse"

                        f_date, f_time, iso_dt, ts = _parse_ff_datetime(cur_date, cur_time, base_year, tz_offset_hours)

                        raw_id = row.get("data-event-id", "").strip()
                        if raw_id:
                            event_id = f"ff_{raw_id}"
                        elif ts:
                            event_id = f"ff_{ts}_{currency}"
                        else:
                            fallback_hash = hashlib.md5(f"{t_cell.text.strip()}_{f_date}_{f_time}_{currency}".encode("utf-8")).hexdigest()[:10]
                            event_id = f"ff_{fallback_hash}"

                        events.append({
                            "id": event_id,
                            "title": t_cell.text.strip(),
                            "country": currency,
                            "datetime": iso_dt,
                            "timestamp": ts,
                            "date": f_date,
                            "time": f_time,
                            "timezone": "UTC",
                            "impact": impact,
                            "forecast": forecast_val,
                            "consensus": forecast_val,
                            "previous": pv.text.strip() if pv else "",
                            "actual": actual_val,
                            "actual_state": actual_state,
                            "raw_date": f"{cur_date} {cur_time}".strip()
                        })
                    events.sort(key=lambda x: (x.get("timestamp") or 0, x.get("title", "")))
                    return events
                elif r.status_code in [403, 429]:
                    time.sleep(2 * attempt)
                else:
                    time.sleep(1)
            except Exception as e:
                print(f"[ForexFactory] Scrape attempt {attempt} error for {url}: {e}")
                time.sleep(1.5 * attempt)
        return []
