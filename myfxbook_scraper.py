from curl_cffi import requests
from bs4 import BeautifulSoup
import time

class MyfxbookScraper:
    def __init__(self):
        self.base_url = "https://www.myfxbook.com/forex-economic-calendar"
        self.impersonate = "chrome124"

    def _scrape_period(self, period_id):
        """Scrape economic calendar for a specific calPeriod"""
        url = f"{self.base_url}?calPeriod={period_id}"
        events = []
        try:
            r = requests.get(url, impersonate=self.impersonate, timeout=20)
            if r.status_code != 200:
                print(f"[Myfxbook] Status {r.status_code} for period {period_id}")
                return []

            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table", {"id": "economicCalendarTable"})
            if not table:
                print(f"[Myfxbook] Table not found for period {period_id}")
                return []

            current_date = ""
            for tr in table.find_all("tr"):
                classes = tr.get("class", [])
                if "economicCalendarDateRow" in classes:
                    current_date = tr.text.strip()
                elif "economicCalendarRow" in classes:
                    tds = tr.find_all("td")
                    if len(tds) >= 9:
                        time_str = tds[0].text.strip()
                        currency = tds[3].text.strip()
                        title = tds[4].text.strip().replace("\n", " ")
                        impact = tds[5].text.strip()
                        previous = tds[6].text.strip()
                        consensus = tds[7].text.strip()
                        actual = tds[8].text.strip()

                        # Normalize title whitespace
                        title = " ".join(title.split())

                        events.append({
                            "title": title,
                            "country": currency,
                            "date": current_date,
                            "time": time_str,
                            "impact": impact,
                            "previous": previous,
                            "consensus": consensus,
                            "actual": actual
                        })
        except Exception as e:
            print(f"[Myfxbook] Error scraping period {period_id}: {e}")

        return events

    def get_this_week(self):
        """Scrape this week's events (calPeriod=3)"""
        return self._scrape_period(3)

    def get_21_days(self):
        """Scrape 3 weeks (21 days) by combining periods (past week, current week, and upcoming 2 weeks)"""
        # calPeriod: 2 (last week), 3 (this week), 9 (next week), 12 (upcoming 2 weeks)
        periods = [2, 3, 9, 12]
        all_events = []
        seen = set()

        for p in periods:
            events = self._scrape_period(p)
            for ev in events:
                key = (ev.get("date"), ev.get("time"), ev.get("country"), ev.get("title"))
                if key not in seen:
                    seen.add(key)
                    all_events.append(ev)
            time.sleep(1) # Polite delay between requests

        return all_events
