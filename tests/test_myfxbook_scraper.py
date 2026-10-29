import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from myfxbook_scraper import MyfxbookScraper

FEED_KEYS = {
    "id", "title", "country", "datetime", "timestamp", "date", "time", "timezone",
    "impact", "forecast", "consensus", "previous", "actual", "actual_state", "raw_date",
}

# Trimmed from the live Myfxbook calendar table (times are rendered in GMT)
PAGE = """<table id="economicCalendarTable">
<tr class="economicCalendarDateRow"><td>Friday, Oct 30, 2026</td></tr>
<tr id="calRow315081" data-row-id="315081" class="economicCalendarRow">
  <td class="calendarToggleCell">Oct 30, 03:00</td><td>22h 53min</td><td></td><td>JPY</td>
  <td class="text-left">BoJ Interest Rate
     Decision</td><td>High</td><td>1.25%</td><td>1.25%</td>
  <td class="background-transparent-green calendarToggleCell"><span class="actualCell">1.5%</span></td><td></td>
</tr>
<tr id="calRow313425" data-row-id="313425" class="economicCalendarRow">
  <td>Oct 30, 00:00</td><td></td><td></td><td>CNY</td><td>Bank Holiday</td><td>None</td>
  <td></td><td></td><td></td><td></td>
</tr>
</table>"""


class ParseHtmlTests(unittest.TestCase):
    def setUp(self):
        self.events = {e["title"]: e for e in MyfxbookScraper()._parse_html(PAGE)}

    def test_boj_decision_parsed_in_utc(self):
        ev = self.events["BoJ Interest Rate Decision"]
        self.assertEqual((ev["id"], ev["date"], ev["time"], ev["datetime"]),
                         ("mfb_315081", "2026-10-30", "03:00", "2026-10-30T03:00:00Z"))
        self.assertEqual((ev["impact"], ev["previous"], ev["forecast"], ev["actual"], ev["actual_state"]),
                         ("High", "1.25%", "1.25%", "1.5%", "better"))
        self.assertEqual(ev["raw_date"], "Friday, Oct 30, 2026")

    def test_holiday_impact(self):
        self.assertEqual(self.events["Bank Holiday"]["impact"], "Non-Economic")

    def test_output_schema_is_unchanged(self):
        for ev in self.events.values():
            self.assertEqual(set(ev), FEED_KEYS)


class TwentyOneDayTests(unittest.TestCase):
    def test_missing_week_is_never_published(self):
        import tempfile
        import myfxbook_scraper as mfs
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(mfs, "CACHE_DIR", tmp), \
                mock.patch.object(mfs.time, "sleep"):
            scraper = MyfxbookScraper()
            periods = {2: [{"id": "mfb_1", "timestamp": 1}], 3: [{"id": "mfb_2", "timestamp": 2}], 9: []}
            scraper._scrape_period = mock.Mock(side_effect=lambda p: periods[p])
            self.assertEqual(scraper.get_21_days(), [])


class FetchTests(unittest.TestCase):
    def test_timezone_cookies_are_pinned_to_gmt_before_each_navigation(self):
        # Regression: after the first load Myfxbook rendered later periods in the browser's offset (IST)
        calls = []
        sb = mock.Mock()
        sb.cdp.evaluate.side_effect = lambda js: calls.append(("pin", js))
        sb.activate_cdp_mode.side_effect = lambda url: calls.append(("open", url))
        sb.get_title.return_value = "Economic Calendar"
        sb.is_element_present.return_value = True
        sb.get_page_source.return_value = PAGE

        scraper = MyfxbookScraper()
        scraper._get_sb = mock.Mock(return_value=sb)
        for period in (3, 2, 9):
            self.assertEqual(scraper._fetch_html_uc(period), PAGE)

        self.assertEqual([c[0] for c in calls], ["pin", "open"] * 3)
        self.assertIn("timezone=0", calls[0][1])
        self.assertIn("dst=0", calls[0][1])


if __name__ == "__main__":
    unittest.main()
