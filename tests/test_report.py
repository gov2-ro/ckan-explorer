"""Tests for report.py. Run: python3 -m unittest discover tests"""
import importlib.util
import json
import os
import re
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("report", os.path.join(HERE, "..", "report.py"))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)
FIXTURE = os.path.join(HERE, "fixtures", "stats-mini")
DATA_RE = re.compile(r'<script id="data" type="application/json">(.*?)</script>', re.S)


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.portal = report.load_portal(os.path.join(FIXTURE, "mini.example", "stats"))

    def build(self, host="mini.example"):
        return report.portal_page(host, self.portal)

    def test_titles_are_escaped(self):
        page = self.build()
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertNotIn("Title <b>", page)
        self.assertIn("Alpha \\u003cscript>alert(1)", page)
        # '&' in the data is valid inside JSON; the page has no raw dataset HTML
        index = report.index_page({"mini.example": self.portal})
        self.assertNotIn("<script>alert", index)
        self.assertNotIn("innerHTML", page)
        self.assertEqual(report.html.escape("A & <B>"), "A &amp; &lt;B&gt;")

    def test_embedded_json_escapes_lt(self):
        page = self.build()
        raw = DATA_RE.search(page).group(1)
        self.assertNotIn("<", raw)
        data = json.loads(raw)
        self.assertIn("<script>alert(1)</script>", data["orgs"][0]["t"])

    def test_output_deterministic(self):
        outs = []
        for name in ("a", "b"):
            out = os.path.join(self.tmp, name)
            os.makedirs(out)
            report.write(os.path.join(out, "x.html"), self.build())
            report.write(os.path.join(out, "index.html"), report.index_page({"mini.example": self.portal}))
            blobs = []
            for f in ("x.html", "index.html"):
                with open(os.path.join(out, f), "rb") as fh:
                    blobs.append(fh.read())
            outs.append(blobs)
        self.assertEqual(outs[0], outs[1])

    def test_view_rows_union_of_top_by_uploads_and_datasets(self):
        orgs, monthly = [], []
        for i in range(60):
            name = "o%02d" % i
            # uploads rise with i; datasets fall with i
            orgs.append({"org_name": name, "org_title": name, "datasets": str(1000 - i)})
            monthly.append({"org_name": name, "month": "2026-10", "uploads": str(i + 1),
                            "updates": "0", "datasets": "1"})
        orgs.append({"org_name": "zero", "org_title": "zero", "datasets": "5000"})  # no uploads
        cols = {"all": ["2026"], "y5": report.window_months("2026-10-15", 60),
                "m12": report.window_months("2026-10-15", 12)}
        rows = report.select_rows(cols, orgs, monthly)
        names = {orgs[i]["org_name"] for i in rows["m12"]}
        self.assertEqual(names, {"o%02d" % i for i in range(60)})  # top 50 up (10..59) + top 50 ds (0..49)
        self.assertNotIn("zero", names)
        self.assertEqual(len(rows["m12"]), len(set(rows["m12"])))
        # a window without uploads leaves the org out
        old = [{"org_name": "o00", "month": "2019-01", "uploads": "4", "updates": "0", "datasets": "1"}]
        rows = report.select_rows(cols, orgs[:1], old)
        self.assertEqual(rows["m12"], [])
        self.assertEqual(rows["all"], [])  # 2019 is outside the 'all' column list given here

    def test_windows_end_at_as_of_month(self):
        w = report.window_months("2026-10-27", 12)
        self.assertEqual((len(w), w[0], w[-1]), (12, "2025-11", "2026-10"))
        w = report.window_months("2026-01-02", 60)
        self.assertEqual((len(w), w[0], w[-1]), (60, "2021-02", "2026-01"))
        data = json.loads(DATA_RE.search(self.build()).group(1))
        self.assertEqual(data["views"]["m12"]["cols"][-1], "2026-10")
        self.assertEqual(data["views"]["all"]["cols"][0], "2018")
        self.assertEqual(data["views"]["all"]["cols"][-1], "2026")

    def test_no_external_resources(self):
        for page in (self.build(), report.index_page({"mini.example": self.portal})):
            for tag in re.findall(r"<(?:script|link)\b[^>]*>", page):
                self.assertNotRegex(tag, r"(src|href)\s*=")
            self.assertNotRegex(page, r"@import|url\(")

    def test_hdx_note_present(self):
        page = self.build("data.humdata.org")
        self.assertIn("created", page)
        self.assertIn("probably reset when a file is replaced", page)
        self.assertNotIn("probably reset", self.build("mini.example"))


if __name__ == "__main__":
    unittest.main()
