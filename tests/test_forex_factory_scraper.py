import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import forex_factory_scraper as ffs

FEED_KEYS = {
    "id", "title", "country", "datetime", "timestamp", "date", "time", "timezone",
    "impact", "forecast", "consensus", "previous", "actual", "actual_state", "raw_date",
}

# Real records captured from forexfactory.com (week of Oct 25 2026 and Nov 1 2026, rendered in UTC)
DAYS = [
    {"date": "Sun <span>Oct 25</span>", "events": [
        {"id": 147447, "name": "Bank Holiday", "currency": "NZD", "dateline": 1792954800, "timeLabel": "All Day",
         "date": "Oct 25, 2026", "impactName": "holiday", "actual": "", "forecast": "", "previous": "",
         "revision": "", "actualBetterWorse": 0},
    ]},
    {"date": "Mon <span>Oct 26</span>", "events": [
        {"id": 149955, "name": "SPPI y/y", "currency": "JPY", "dateline": 1793058600, "timeLabel": "11:50pm",
         "date": "Oct 26, 2026", "impactName": "low", "actual": "3.7%", "forecast": "3.7%", "previous": "3.7%",
         "revision": "3.5%", "actualBetterWorse": 0},
    ]},
    {"date": "Thu <span>Oct 29</span>", "events": [
        {"id": 149931, "name": "Tokyo Core CPI y/y", "currency": "JPY", "dateline": 1793316600, "timeLabel": "11:30pm",
         "date": "Oct 29, 2026", "impactName": "medium", "actual": "2.8%", "forecast": "2.6%", "previous": "2.7%",
         "revision": "", "actualBetterWorse": 1},
    ]},
    {"date": "Fri <span>Oct 30</span>", "events": [
        {"id": 148562, "name": "BOJ Policy Rate", "currency": "JPY", "dateline": 1793327400, "timeLabel": "Tentative",
         "date": "Oct 30, 2026", "impactName": "high", "actual": "", "forecast": "<1.25%", "previous": "<1.25%",
         "revision": "", "actualBetterWorse": 0},
        {"id": 151201, "name": "German Prelim CPI m/m", "currency": "EUR", "dateline": 1793345340, "timeLabel": "All Day",
         "date": "Oct 30, 2026", "impactName": "medium", "actual": "-0.1%", "forecast": "0.1%", "previous": "0.6%",
         "revision": "", "actualBetterWorse": 2},
    ]},
    {"date": "Fri <span>Nov 6</span>", "events": [
        {"id": 146914, "name": "Non-Farm Employment Change", "currency": "USD", "dateline": 1793971800,
         "timeLabel": "1:30pm", "date": "Nov 6, 2026", "impactName": "high", "actual": "", "forecast": "",
         "previous": "29K", "revision": "", "actualBetterWorse": 0},
        {"id": 999001, "name": "IMF Meetings", "currency": "All", "dateline": 1794000000, "timeLabel": "Day 3",
         "date": "Nov 6, 2026", "impactName": "low", "actual": "", "forecast": "", "previous": "",
         "revision": "", "actualBetterWorse": 0},
    ]},
]


def _page(days, timezone_name="Etc/UTC"):
    """Build a minimal calendar page with the same embedded-state layout as forexfactory.com."""
    return (
        "<html><head><script>window.FF = {timezone: '0'.replace('+', ''), "
        f"timezone_name: '{timezone_name}'}};</script></head><body>"
        "<script type=\"text/javascript\">if (typeof window.calendarComponentStates === 'undefined') "
        "{ window.calendarComponentStates = {} }\nwindow.calendarComponentStates[1] = {\n"
        f"days: {json.dumps(days)},\ntime: 1793246681}};</script></body></html>"
    )


def _by_title(events):
    return {e["title"]: e for e in events}


class ParseCalendarJsonTests(unittest.TestCase):
    def setUp(self):
        self.events = _by_title(ffs.ForexFactoryScraper()._parse_html(_page(DAYS)))

    def test_tentative_event_uses_real_release_instant(self):
        # Regression: BOJ Policy Rate was anchored to 2026-10-29 (US printed date). FF GMT and Myfxbook say Oct 30.
        ev = self.events["BOJ Policy Rate"]
        self.assertEqual(ev["date"], "2026-10-30")
        self.assertEqual(ev["time"], "Tentative")
        self.assertEqual(ev["datetime"], "2026-10-30T02:30:00Z")
        self.assertEqual(ev["timestamp"], 1793327400)
        self.assertEqual(ev["raw_date"], "Fri Oct 30 Tentative")

    def test_all_day_event_keeps_printed_date_at_utc_midnight(self):
        # All Day datelines are placeholders (07:29 here) and must not move the event
        ev = self.events["German Prelim CPI m/m"]
        self.assertEqual(ev["date"], "2026-10-30")
        self.assertEqual(ev["time"], "All Day")
        self.assertEqual(ev["datetime"], "2026-10-30T00:00:00Z")

        holiday = self.events["Bank Holiday"]
        self.assertEqual(holiday["datetime"], "2026-10-25T00:00:00Z")
        self.assertEqual(holiday["impact"], "Non-Economic")

    def test_multi_day_label_is_treated_like_all_day(self):
        ev = self.events["IMF Meetings"]
        self.assertEqual((ev["date"], ev["time"], ev["datetime"]), ("2026-11-06", "Day 3", "2026-11-06T00:00:00Z"))

    def test_timed_event_after_us_dst_change_is_exact(self):
        # Regression: a single page offset (-7) put NFP at 12:30Z after US DST ended on Nov 1
        ev = self.events["Non-Farm Employment Change"]
        self.assertEqual((ev["date"], ev["time"], ev["datetime"]), ("2026-11-06", "13:30", "2026-11-06T13:30:00Z"))

    def test_late_utc_event_stays_on_its_utc_day(self):
        ev = self.events["Tokyo Core CPI y/y"]
        self.assertEqual((ev["date"], ev["time"]), ("2026-10-29", "23:30"))

    def test_value_fields(self):
        cpi = self.events["Tokyo Core CPI y/y"]
        self.assertEqual((cpi["impact"], cpi["actual_state"], cpi["forecast"], cpi["consensus"]),
                         ("Medium", "better", "2.6%", "2.6%"))
        self.assertEqual(self.events["German Prelim CPI m/m"]["actual_state"], "worse")
        self.assertEqual(self.events["BOJ Policy Rate"]["impact"], "High")
        # FF shows the revised previous value when one exists
        self.assertEqual(self.events["SPPI y/y"]["previous"], "3.5%")

    def test_output_schema_is_unchanged(self):
        for ev in self.events.values():
            self.assertEqual(set(ev), FEED_KEYS)
            self.assertEqual(ev["timezone"], "UTC")
            self.assertTrue(ev["id"].startswith("ff_"))

    def test_events_are_sorted_chronologically(self):
        events = ffs.ForexFactoryScraper()._parse_html(_page(DAYS))
        stamps = [e["timestamp"] for e in events]
        self.assertEqual(stamps, sorted(stamps))


class HtmlFallbackTests(unittest.TestCase):
    def test_falls_back_to_table_when_embedded_json_is_missing(self):
        html = """<script>window.FF = {timezone: '0'};</script><table>
        <tr class="calendar__row" data-event-id="148562">
          <td class="calendar__date"><span class="date">Fri <span>Oct 30</span></span></td>
          <td class="calendar__time">Tentative</td><td class="calendar__currency">JPY</td>
          <td class="calendar__impact"><span class="icon icon--ff-impact-red"></span></td>
          <td><span class="calendar__event-title">BOJ Policy Rate</span></td>
          <td class="calendar__actual"></td><td class="calendar__forecast">&lt;1.25%</td>
          <td class="calendar__previous">&lt;1.25%</td></tr>
        <tr class="calendar__row" data-event-id="149931">
          <td class="calendar__time">11:30pm</td><td class="calendar__currency">JPY</td>
          <td class="calendar__impact"><span class="icon icon--ff-impact-ora"></span></td>
          <td><span class="calendar__event-title">Tokyo Core CPI y/y</span></td>
          <td class="calendar__actual"><span class="better">2.8%</span></td>
          <td class="calendar__forecast">2.6%</td><td class="calendar__previous">2.7%</td></tr>
        </table>"""
        with mock.patch.object(ffs, "datetime", wraps=ffs.datetime) as dt:
            dt.now.return_value = ffs.datetime(2026, 10, 29, tzinfo=ffs.timezone.utc)
            events = _by_title(ffs.ForexFactoryScraper()._parse_html(html))
        self.assertEqual(events["BOJ Policy Rate"]["datetime"], "2026-10-30T00:00:00Z")
        self.assertEqual(events["BOJ Policy Rate"]["forecast"], "<1.25%")
        cpi = events["Tokyo Core CPI y/y"]
        self.assertEqual((cpi["datetime"], cpi["impact"], cpi["actual_state"]), ("2026-10-30T23:30:00Z", "Medium", "better"))
        self.assertEqual(set(cpi), FEED_KEYS)


class FetchTests(unittest.TestCase):
    def test_requests_calendar_in_utc(self):
        scraper = ffs.ForexFactoryScraper()
        response = mock.Mock(status_code=200, text=_page(DAYS))
        scraper.session = mock.Mock(get=mock.Mock(return_value=response))
        events = scraper._scrape_html_calendar("week=this")
        self.assertEqual(len(events), 7)
        kwargs = scraper.session.get.call_args.kwargs
        self.assertEqual(kwargs["cookies"], {"fftimezone": "Etc%2FUTC"})

    def test_retries_when_page_has_no_events(self):
        scraper = ffs.ForexFactoryScraper()
        challenge = mock.Mock(status_code=200, text="<html><title>Just a moment...</title></html>")
        good = mock.Mock(status_code=200, text=_page(DAYS))
        scraper.session = mock.Mock(get=mock.Mock(side_effect=[challenge, good]))
        with mock.patch.object(ffs.time, "sleep"):
            events = scraper._scrape_html_calendar("week=this")
        self.assertEqual(len(events), 7)
        self.assertEqual(scraper.session.get.call_count, 2)


class ImpactTests(unittest.TestCase):
    def test_falls_back_to_folder_icon_class(self):
        self.assertEqual(ffs._ff_impact({"impactName": "red-folder", "impactClass": "icon--ff-impact-red"}), "High")
        self.assertEqual(ffs._ff_impact({"impactName": "", "impactClass": "icon--ff-impact-gra"}), "Non-Economic")
        self.assertEqual(ffs._ff_impact({"impactName": "?", "impactClass": "?"}), "Low")


class TwentyOneDayTests(unittest.TestCase):
    def test_missing_week_is_never_published(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(ffs, "CACHE_DIR", tmp), \
                mock.patch.object(ffs.time, "sleep"):
            scraper = ffs.ForexFactoryScraper()
            week = {"week=last": [{"id": "ff_1", "timestamp": 1}], "week=this": [{"id": "ff_2", "timestamp": 2}],
                    "week=next": []}
            scraper._scrape_html_calendar = mock.Mock(side_effect=lambda q: week[q])
            self.assertEqual(scraper.get_21_days(), [])

            week["week=next"] = [{"id": "ff_3", "timestamp": 3}]
            self.assertEqual([e["id"] for e in scraper.get_21_days()], ["ff_1", "ff_2", "ff_3"])


class WeekCacheTests(unittest.TestCase):
    def test_week_key_is_sunday_of_utc_week(self):
        with mock.patch.object(ffs, "datetime", wraps=ffs.datetime) as dt:
            dt.now.return_value = ffs.datetime(2026, 10, 29, 12, tzinfo=ffs.timezone.utc)  # Thursday
            self.assertEqual(ffs._week_key(0), "2026-10-25")
            self.assertEqual(ffs._week_key(-1), "2026-10-18")
            self.assertEqual(ffs._week_key(1), "2026-11-01")
            dt.now.return_value = ffs.datetime(2026, 11, 1, 0, 5, tzinfo=ffs.timezone.utc)  # Sunday
            self.assertEqual(ffs._week_key(0), "2026-11-01")

    def test_fallback_cache_never_serves_a_different_week(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(ffs, "CACHE_DIR", tmp):
            scraper = ffs.ForexFactoryScraper()
            scraper._write_cache("this_week_2026-10-18", [{"id": "ff_old"}])
            scraper._scrape_html_calendar = mock.Mock(return_value=[])
            with mock.patch.object(ffs, "_week_key", return_value="2026-10-25"):
                self.assertEqual(scraper.get_this_week(), [])
                scraper._write_cache("this_week_2026-10-25", [{"id": "ff_new"}])
                self.assertEqual(scraper.get_this_week(), [{"id": "ff_new"}])


if __name__ == "__main__":
    unittest.main()
