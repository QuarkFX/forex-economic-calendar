import os
import re
import json
import time
import hashlib
from datetime import datetime, timezone, timedelta
from curl_cffi import requests
from bs4 import BeautifulSoup

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT_DIR, ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

# Forex Factory picks the display timezone from the visitor's IP (US Pacific on GitHub runners)
# unless this cookie is set. Rendering in UTC makes the printed day of every event, including
# "All Day" events, match the Forex Factory GMT view regardless of where the scraper runs.
FF_TIMEZONE_COOKIES = {"fftimezone": "Etc%2FUTC"}

IMPACT_MAP = {"high": "High", "medium": "Medium", "low": "Low", "holiday": "Non-Economic"}
IMPACT_CLASS_MAP = (("impact-red", "High"), ("impact-ora", "Medium"), ("impact-yel", "Low"), ("impact-gra", "Non-Economic"))
ACTUAL_STATE_MAP = {1: "better", 2: "worse"}

def _ff_impact(ev):
    """Map FF impact to the feed rating, falling back to the folder icon class so red folders are never downgraded silently."""
    name = (ev.get("impactName") or "").lower()
    if name in IMPACT_MAP:
        return IMPACT_MAP[name]
    icon_class = (ev.get("impactClass") or "").lower()
    for key, impact in IMPACT_CLASS_MAP:
        if key in icon_class:
            return impact
    print(f"[ForexFactory] Warning: unknown impact {name!r}/{icon_class!r} for {ev.get('name')!r}. Defaulting to Low.")
    return "Low"

def _week_key(offset_weeks=0):
    """Return the Sunday (UTC) that starts the target calendar week, used to scope caches per week."""
    today = datetime.now(timezone.utc).date()
    sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    return (sunday + timedelta(weeks=offset_weeks)).isoformat()

def _extract_calendar_days(html_text):
    """Extract the `days` array embedded in window.calendarComponentStates on the calendar page."""
    marker = re.search(r'calendarComponentStates\[\d+\]\s*=\s*\{\s*days:\s*', html_text or "")
    if not marker:
        return None
    try:
        days, _ = json.JSONDecoder().raw_decode(html_text, marker.end())
    except ValueError:
        return None
    return days if isinstance(days, list) else None

def _ff_event_datetime(time_label, dateline, date_str):
    """
    Resolve an embedded FF event into (date, time, iso, epoch) in UTC.

    Timed and "Tentative" events carry their real release instant in `dateline`, which is
    timezone independent. "All Day" / "Day N" events have a placeholder dateline, so they stay
    anchored to UTC midnight of the calendar date FF prints for them.
    """
    label = (time_label or "").strip()
    is_timed = bool(re.match(r'\d{1,2}:\d{2}', label))
    if (is_timed or label.lower() == "tentative") and dateline:
        dt_utc = datetime.fromtimestamp(int(dateline), timezone.utc)
        f_time = dt_utc.strftime("%H:%M") if is_timed else label
    else:
        day = datetime.strptime(date_str, "%b %d, %Y")
        dt_utc = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        f_time = label or "All Day"
    return dt_utc.strftime("%Y-%m-%d"), f_time, dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), int(dt_utc.timestamp())

def _parse_calendar_json(days):
    """Build feed events from the embedded calendar JSON."""
    events = []
    for day in days or []:
        day_label = re.sub(r'<[^>]+>', '', day.get("date", "")).strip()
        for ev in day.get("events", []):
            title = (ev.get("name") or "").strip()
            time_label = (ev.get("timeLabel") or "").strip()
            try:
                f_date, f_time, iso_dt, ts = _ff_event_datetime(time_label, ev.get("dateline"), ev.get("date", ""))
            except (ValueError, TypeError, OverflowError):
                print(f"[ForexFactory] Skipping event with unparseable date: {title!r} {ev.get('date')!r}")
                continue

            forecast_val = ev.get("forecast") or ""
            events.append({
                "id": f"ff_{ev.get('id')}",
                "title": title,
                "country": ev.get("currency") or "",
                "datetime": iso_dt,
                "timestamp": ts,
                "date": f_date,
                "time": f_time,
                "timezone": "UTC",
                "impact": _ff_impact(ev),
                "forecast": forecast_val,
                "consensus": forecast_val,
                # FF displays the revised previous value when one exists
                "previous": ev.get("revision") or ev.get("previous") or "",
                "actual": ev.get("actual") or "",
                "actual_state": ACTUAL_STATE_MAP.get(ev.get("actualBetterWorse"), "neutral"),
                "raw_date": f"{day_label} {time_label}".strip()
            })
    events.sort(key=lambda x: (x.get("timestamp") or 0, x.get("title", "")))
    return events

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
            now_month = datetime.now(timezone.utc).month
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
                # Anchor to UTC midnight of the printed date. This is only correct when the page
                # was rendered in UTC (see FF_TIMEZONE_COOKIES); the JSON path is preferred.
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
        cache_key = f"this_week_{_week_key(0)}"
        if not force_refresh:
            cached = self._read_cache(cache_key, 300)
            if cached:
                return cached

        fresh = self._scrape_html_calendar("week=this")
        if fresh:
            self._write_cache(cache_key, fresh)
            return fresh

        # Direct cache fallback to protect live actuals (same calendar week only)
        return self._read_cache(cache_key, 86400) or []

    def get_21_days(self):
        """Fetch 21 consecutive days (Previous Week + This Week + Next Week) with resilient fallback."""
        # Cache keys are scoped to the target week so a week rollover never serves the wrong week
        last_key = f"last_week_{_week_key(-1)}"
        next_key = f"next_week_{_week_key(1)}"

        # Previous Week (24h cache)
        last_week = self._read_cache(last_key, 86400)
        if not last_week:
            last_week = self._scrape_html_calendar("week=last")
            if last_week:
                self._write_cache(last_key, last_week)
            time.sleep(1)

        # This Week (reuses live data from current cycle, no duplicate request)
        this_week = self.get_this_week(force_refresh=False)

        # Next Week (2h cache)
        next_week = self._read_cache(next_key, 7200)
        if not next_week:
            next_week = self._scrape_html_calendar("week=next")
            if next_week:
                self._write_cache(next_key, next_week)
            time.sleep(1)

        # Resilient fallback: If live scrape failed, reuse last known good cache up to 7 days
        if not last_week:
            last_week = self._read_cache(last_key, 86400 * 7) or []
        if not next_week:
            next_week = self._read_cache(next_key, 86400 * 7) or []

        # Never publish a 21-day feed with a missing week (e.g. no upcoming news); the previous file is kept instead
        if not (last_week and this_week and next_week):
            print(f"[ForexFactory] Incomplete 21-day dataset (last={len(last_week)}, this={len(this_week)}, next={len(next_week)}). Skipping update.")
            return []

        return _dedup_events(last_week, this_week, next_week)

    def _parse_html(self, html_text):
        """Extract events from the embedded calendar JSON, falling back to the rendered HTML table."""
        days = _extract_calendar_days(html_text)
        if days is not None:
            return _parse_calendar_json(days)
        print("[ForexFactory] Embedded calendar JSON not found. Falling back to HTML table parsing.")
        return self._parse_html_table(html_text)

    def _parse_html_table(self, html_text):
        """Legacy parser for the rendered calendar table. Requires the page to be rendered in UTC for exact dates."""
        # Extract rendered timezone offset from window.FF configuration
        tz_offset_hours = 0.0
        tz_match = re.search(r'timezone:\s*[\'"]([+-]?\d+(?:\.\d+)?)', html_text)
        if tz_match:
            try:
                tz_offset_hours = float(tz_match.group(1).replace('+', ''))
            except (ValueError, TypeError):
                tz_offset_hours = 0.0

        soup = BeautifulSoup(html_text, "html.parser")
        events, cur_date, cur_time = [], "", ""
        base_year = datetime.now(timezone.utc).year

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

    def _scrape_html_calendar(self, query, max_retries=3):
        url = f"{self.base_url}?{query}"
        for attempt in range(1, max_retries + 1):
            try:
                r = self.session.get(url, impersonate="safari15_3", timeout=25, cookies=FF_TIMEZONE_COOKIES)
                if r.status_code == 200:
                    tz_name = re.search(r"timezone_name:\s*'([^']*)'", r.text)
                    if tz_name and tz_name.group(1) != "Etc/UTC":
                        print(f"[ForexFactory] Warning: page rendered in {tz_name.group(1)} instead of UTC for {url}")
                    events = self._parse_html(r.text)
                    if events:
                        return events
                    # A 200 page without events is usually a bot challenge; retry instead of giving up
                    print(f"[ForexFactory] No events parsed from {url} (attempt {attempt}).")
                    time.sleep(2 * attempt)
                elif r.status_code in [403, 429]:
                    time.sleep(2 * attempt)
                else:
                    time.sleep(1)
            except Exception as e:
                print(f"[ForexFactory] Scrape attempt {attempt} error for {url}: {e}")
                time.sleep(1.5 * attempt)
        return []
