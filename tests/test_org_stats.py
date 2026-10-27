"""Tests for org-stats.py. Run: python3 -m unittest discover tests"""
import csv
import importlib.util
import json
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("org_stats", os.path.join(HERE, "..", "org-stats.py"))
org_stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(org_stats)
FIXTURE = os.path.join(HERE, "fixtures", "mini.jsonl")


def rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class OrgStatsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.pdir = os.path.join(self.tmp, "mini.example")
        os.makedirs(self.pdir)
        shutil.copy(FIXTURE, os.path.join(self.pdir, "datasets.jsonl"))
        self.summary = org_stats.process(self.pdir)
        self.out = os.path.join(self.pdir, "stats")
        self.orgs = {r["org_name"]: r for r in rows(os.path.join(self.out, "orgs.csv"))}
        self.datasets = {r["id"]: r for r in rows(os.path.join(self.out, "datasets.csv"))}

    def test_no_org_grouped_as_none(self):
        self.assertIn("_none", self.orgs)
        self.assertEqual(self.orgs["_none"]["org_title"], "(no organization)")
        self.assertEqual(self.orgs["_none"]["datasets"], "1")
        self.assertEqual(self.summary["no_org_datasets"], 1)
        self.assertEqual(self.summary["orgs"], 2)  # _none not counted

    def test_upload_requires_valid_created(self):
        b = self.datasets["b"]
        self.assertEqual(b["resources"], "4")
        self.assertEqual(b["uploads"], "2")
        self.assertEqual(self.summary["resources_no_created"], 1)
        self.assertEqual(self.summary["resources_invalid_created"], 1)

    def test_update_counted_after_one_day(self):
        # b: +1 day exactly is not an update; +56 days is. c: lm before created, not an update.
        self.assertEqual(self.datasets["b"]["updates"], "1")
        self.assertEqual(self.summary["last_modified_after_created_1d"], 1)
        self.assertEqual(self.summary["last_modified_before_created_1d"], 1)
        monthly = rows(os.path.join(self.out, "org-monthly.csv"))
        m = [r for r in monthly if r["org_name"] == "org-two" and r["month"] == "2024-03"]
        self.assertEqual(len(m), 1)
        self.assertEqual((m[0]["uploads"], m[0]["updates"], m[0]["datasets"]), ("0", "1", "0"))

    def test_window_12m_and_60m_boundaries(self):
        # as-of 2026-06: 12m = 2025-07..2026-06; 60m = 2021-07..2026-06.
        o = self.orgs["org-one"]
        self.assertEqual(o["uploads"], "5")
        self.assertEqual(o["uploads_12m"], "2")   # 2026-06-10, 2025-07-01
        self.assertEqual(o["uploads_60m"], "4")   # 2025-06-30 and 2021-07-01 in; 2021-06-30 out
        self.assertEqual(o["datasets_12m"], "1")

    def test_duplicate_id_kept_once_and_counted(self):
        self.assertEqual(self.summary["duplicate_ids"], 1)
        self.assertEqual(self.summary["datasets"], 4)
        self.assertEqual(self.datasets["a"]["name"], "pkg-a")  # first line kept
        self.assertEqual(self.summary["resources"], 10)

    def test_as_of_from_max_metadata_modified(self):
        self.assertEqual(self.summary["as_of"], "2026-06-15")
        s = org_stats.process(self.pdir, "2024-03-31")
        self.assertEqual(s["as_of"], "2024-03-31")

    def test_invariants_hold_on_fixture(self):
        self.assertTrue(all(self.summary["invariants"].values()), self.summary["invariants"])
        self.assertEqual(sum(int(r["datasets"]) for r in self.orgs.values()), self.summary["datasets"])
        self.assertEqual(sum(int(r["resources"]) for r in self.orgs.values()), self.summary["resources"])
        monthly = rows(os.path.join(self.out, "org-monthly.csv"))
        self.assertEqual(sum(int(r["uploads"]) for r in monthly),
                         sum(int(r["uploads"]) for r in self.orgs.values()))
        for r in self.orgs.values():
            self.assertLessEqual(int(r["uploads_12m"]), int(r["uploads_60m"]))
            self.assertLessEqual(int(r["uploads_60m"]), int(r["uploads"]))

    def test_output_sorted_and_deterministic(self):
        names = ["orgs.csv", "org-monthly.csv", "datasets.csv", "summary.json"]
        def read_all():
            out = []
            for n in names:
                with open(os.path.join(self.out, n), "rb") as f:
                    out.append(f.read())
            return out
        first = read_all()
        org_stats.process(self.pdir)
        second = read_all()
        self.assertEqual(first, second)
        orgs = rows(os.path.join(self.out, "orgs.csv"))
        self.assertEqual(orgs, sorted(orgs, key=lambda r: (-int(r["uploads"]), r["org_name"])))
        ids = list(self.datasets)
        self.assertEqual(ids, sorted(ids))


if __name__ == "__main__":
    unittest.main()
