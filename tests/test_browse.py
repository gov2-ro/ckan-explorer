"""Tests for browse.py. Run: python3 -m unittest discover tests"""
import importlib.util
import json
import os
import re
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("browse", os.path.join(HERE, "..", "browse.py"))
browse = importlib.util.module_from_spec(spec)
spec.loader.exec_module(browse)
spec2 = importlib.util.spec_from_file_location("report", os.path.join(HERE, "..", "report.py"))
report = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(report)
STATS = os.path.join(HERE, "fixtures", "stats-mini", "mini.example", "stats")
FIXTURE = os.path.join(HERE, "fixtures", "browse-mini")
JSONL = os.path.join(FIXTURE, "datasets.jsonl")
FIELDS = os.path.join(FIXTURE, "fields.jsonl")
NO_FIELDS = os.path.join(FIXTURE, "absent.jsonl")


class BrowseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def data(self, fields=NO_FIELDS):
        return browse.build_data("mini.example", "https://mini.example", JSONL, fields)

    def test_js_escapes_lt(self):
        js = browse.js_file(self.data())
        self.assertNotIn("<", js)
        self.assertIn("\\u003c", js)

    def page(self, fields=NO_FIELDS):
        d = self.data(fields)
        return report.portal_page("mini.example", report.load_portal(STATS), d)

    def test_page_has_no_data_values(self):
        page = self.page()
        self.assertNotIn("<script>alert", page)
        self.assertNotIn("Second", page)

    def test_output_deterministic(self):
        a = browse.js_file(self.data(FIELDS)) + self.page(FIELDS)
        b = browse.js_file(self.data(FIELDS)) + self.page(FIELDS)
        self.assertEqual(a, b)

    def test_no_external_resources(self):
        page = self.page()
        srcs = re.findall(r'<(?:script|link)[^>]*(?:src|href)="([^"]*)"', page)
        self.assertIn("mini.example-datasets.js", srcs)
        for m in srcs:
            self.assertFalse(m.startswith(("http", "//")), m)

    def test_formats_normalized(self):
        d = self.data()
        self.assertEqual(d["formats"], ["?", "CSV", "XLSX"])

    def test_page_without_browser_data_has_no_section(self):
        page = report.portal_page("mini.example", report.load_portal(STATS))
        self.assertNotIn('id="datasets"', page)

    def test_fields_absent_means_hidden(self):
        d = self.data()
        self.assertFalse(d["has_fields"])
        self.assertFalse(any("fields" in r for ds in d["datasets"] for r in ds["res"]))
        self.assertIn('id="fld" aria-label="Fields" hidden', self.page())

    def test_fields_present_are_embedded(self):
        d = self.data(FIELDS)
        self.assertTrue(d["has_fields"])
        res = [r for ds in d["datasets"] for r in ds["res"] if "fields" in r]
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["fields"], [["col", "text"]])  # _id dropped
        self.assertEqual(res[0]["total"], 7)

    def test_error_records_ignored(self):
        d = self.data(FIELDS)
        first = [ds for ds in d["datasets"] if ds["name"] == "first"][0]
        self.assertNotIn("fields", first["res"][0])

    def test_no_org_and_order(self):
        d = self.data()
        self.assertEqual([ds["name"] for ds in d["datasets"]], ["first", "second"])  # id order b1, b2
        self.assertEqual(d["datasets"][0]["org"], "")
        self.assertEqual(d["orgs"], {"org-a": "Org <script>alert(1)</script>"})

    def test_stats_joined_by_id(self):
        stats = {"b2": {"uploads": "5", "active_months": "3", "first_upload": "2020-01-02",
                        "last_upload": "2021-01-01", "timespan_days": "365"}}
        d = browse.build_data("mini.example", "https://mini.example", JSONL, NO_FIELDS, stats)
        self.assertTrue(d["has_stats"])
        second = [x for x in d["datasets"] if x["name"] == "second"][0]
        first = [x for x in d["datasets"] if x["name"] == "first"][0]
        self.assertEqual((second["up"], second["am"], second["fu"], second["lu"], second["ts"]),
                         (5, 3, "2020-01-02", "2021-01-01", 365))
        self.assertNotIn("up", first)
        self.assertFalse(self.data()["has_stats"])

    def test_feed_not_in_js_file(self):
        self.assertNotIn('"feed"', browse.js_file(self.data()))

    def test_rss_valid_sorted_and_escaped(self):
        import xml.dom.minidom
        feed = browse.rss(self.data())
        dom = xml.dom.minidom.parseString(feed.encode("utf-8"))
        titles = [n.firstChild.data for n in dom.getElementsByTagName("title")][1:]
        self.assertEqual(titles, ["Second <b>set</b> & more", "First"])  # newest first
        self.assertNotIn("<script>alert", feed)
        self.assertIn("Wed, 03 Feb 2021 00:00:00 +0000", feed)

    def test_rss_deterministic_and_limited(self):
        d = self.data()
        self.assertEqual(browse.rss(d), browse.rss(self.data()))
        d["feed"] = d["feed"] * 3
        self.assertEqual(browse.rss(d).count("<item>"), 6)

    def test_page_links_rss_and_drops_top_tables(self):
        page = self.page()
        self.assertIn("mini.example.rss.xml", page)
        self.assertNotIn('id="tbl"', page)
        plain = report.portal_page("mini.example", report.load_portal(STATS))
        self.assertIn('id="tbl"', plain)

    def test_totals_and_org_size(self):
        d = self.data()
        self.assertEqual(d["totals"], {"files": 3, "sized": 2, "bytes": 2058})
        self.assertEqual(d["org_size"], {"org-a": 2048, "_none": 10})
        self.assertEqual(browse.human_size(2058), "2.0 KB")

    def test_zero_no_org_tile_hidden_and_same_uploads_tile_hidden(self):
        portal = report.load_portal(STATS)
        s = portal["summary"]
        s.update({"no_org_datasets": 0, "uploads": s["resources"]})
        page = report.portal_page("mini.example", portal, self.data())
        self.assertNotIn("Datasets with no organization", page)
        self.assertNotIn("<span>Uploads</span>", page)
        self.assertIn("Total file size", page)
        s.update({"no_org_datasets": 2, "uploads": s["resources"] + 1})
        page = report.portal_page("mini.example", portal, self.data())
        self.assertIn("Datasets with no organization", page)
        self.assertIn("<span>Uploads</span>", page)

    def test_values(self):
        d = self.data()
        r = d["datasets"][1]["res"][0]
        self.assertEqual((r["size"], r["fmt"], r["created"], r["ds"]), (2048, "CSV", "2020-01-02", True))
        self.assertEqual(d["datasets"][0]["notes"], "")
        self.assertEqual(d["as_of"], "2021-02-03")


if __name__ == "__main__":
    unittest.main()
