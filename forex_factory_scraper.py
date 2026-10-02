import json
from datetime import datetime, timedelta
from curl_cffi import requests
from bs4 import BeautifulSoup

class ForexFactoryScraper:
    def __init__(self):
        self.faireconomy_url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        self.base_url = "https://www.forexfactory.com/calendar"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def get_this_week(self):
        """Fetch this week's events from Faireconomy JSON or HTML fallback"""
        try:
            r = requests.get(self.faireconomy_url, impersonate="chrome124", timeout=15)
            if r.status_code == 200:
                data = r.json()
                return data
        except Exception as e:
            print(f"[ForexFactory] JSON feed error: {e}, falling back to HTML")

        return self._scrape_html_calendar("week=this")

    def get_21_days(self):
        """Fetch 3 weeks (21 days) of calendar events"""
        events = []
        seen = set()

        # Step 1: Add this week
        this_week = self.get_this_week()
        for ev in this_week:
            key = (ev.get("date"), ev.get("country"), ev.get("title"))
            if key not in seen:
                seen.add(key)
                events.append(ev)

        # Step 2: Next week
        next_week_events = self._scrape_html_calendar("week=next")
        for ev in next_week_events:
            key = (ev.get("date"), ev.get("country"), ev.get("title"))
            if key not in seen:
                seen.add(key)
                events.append(ev)

        # Step 3: Week after next (or current month)
        month_events = self._scrape_html_calendar("month=this")
        for ev in month_events:
            key = (ev.get("date"), ev.get("country"), ev.get("title"))
            if key not in seen:
                seen.add(key)
                events.append(ev)

        # Sort by date
        events.sort(key=lambda x: str(x.get("date", "")))
        return events

    def _scrape_html_calendar(self, query_param):
        """Scrape HTML calendar from forexfactory.com"""
        url = f"{self.base_url}?{query_param}"
        try:
            r = requests.get(url, impersonate="safari15_3", timeout=20)
            if r.status_code != 200:
                print(f"[ForexFactory] Failed to fetch {url}: {r.status_code}")
                return []
            
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.find_all("tr", class_="calendar__row")
            
            events = []
            current_date_str = ""

            for row in rows:
                if "calendar__row--day-breaker" in row.get("class", []):
                    continue

                date_cell = row.find("span", class_="date")
                if date_cell and date_cell.text.strip():
                    current_date_str = date_cell.text.strip()

                title_cell = row.find("span", class_="calendar__event-title")
                if not title_cell:
                    continue

                title = title_cell.text.strip()
                currency_cell = row.find("td", class_="calendar__currency")
                currency = currency_cell.text.strip() if currency_cell else ""

                time_cell = row.find("td", class_="calendar__time")
                time_str = time_cell.text.strip() if time_cell else ""

                impact_cell = row.find("td", class_="calendar__impact")
                impact = "Low"
                if impact_cell:
                    span_impact = impact_cell.find("span")
                    if span_impact and "class" in span_impact.attrs:
                        classes = " ".join(span_impact["class"])
                        if "red" in classes or "high" in classes:
                            impact = "High"
                        elif "orange" in classes or "medium" in classes:
                            impact = "Medium"
                        elif "yellow" in classes or "low" in classes:
                            impact = "Low"
                        elif "gray" in classes or "holiday" in classes:
                            impact = "Non-Economic"

                forecast_cell = row.find("td", class_="calendar__forecast")
                forecast = forecast_cell.text.strip() if forecast_cell else ""

                previous_cell = row.find("td", class_="calendar__previous")
                previous = previous_cell.text.strip() if previous_cell else ""

                actual_cell = row.find("td", class_="calendar__actual")
                actual = actual_cell.text.strip() if actual_cell else ""

                events.append({
                    "title": title,
                    "country": currency,
                    "date": f"{current_date_str} {time_str}".strip(),
                    "impact": impact,
                    "forecast": forecast,
                    "previous": previous,
                    "actual": actual
                })

            return events
        except Exception as e:
            print(f"[ForexFactory] Scrape error for {url}: {e}")
            return []
