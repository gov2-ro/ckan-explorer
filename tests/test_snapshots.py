"""Tests for snapshot.py and diff-snapshots.py. Run: python3 -m unittest discover tests"""
import csv
import gzip
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "..", filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


snapshot = load_module("snapshot", "snapshot.py")
diffmod = load_module("diff_snapshots", "diff-snapshots.py")
OLD = os.path.join(HERE, "fixtures", "snap-old.jsonl")
NEW = os.path.join(HERE, "fixtures", "snap-new.jsonl")
SLIM = ["id", "name", "title", "org_name", "metadata_created", "metadata_modified",
        "num_resources", "resources"]
RES = ["id", "created", "last_modified", "format", "url"]


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def portal(self, name, src):
        d = os.path.join(self.tmp, name)
        os.makedirs(d)
        shutil.copy(src, os.path.join(d, "datasets.jsonl"))
        return d

    def make(self, name, src):
        d = self.portal(name, src)
        s = snapshot.process(d)
        return d, s["path"]

    def read(self, path):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def diff_rows(self):
        _, old = self.make("old", OLD)
        _, new = self.make("new", NEW)
        out = os.path.join(self.tmp, "d.csv")
        argv = sys.argv
        sys.argv = ["diff-snapshots.py", old, new, "--out", out]
        try:
            diffmod.main()
        finally:
            sys.argv = argv
        with open(out, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def test_snapshot_slim_fields_only(self):
        _, path = self.make("p", OLD)
        recs = self.read(path)
        self.assertEqual(len(recs), 4)
        for r in recs:
            self.assertEqual(list(r), SLIM)
            for res in r["resources"]:
                self.assertEqual(list(res), RES)
        self.assertEqual(recs[0]["org_name"], "org1")
        self.assertTrue(path.endswith("2020-04-01.jsonl.gz"))

    def test_snapshot_sorted_and_deterministic(self):
        d, path = self.make("p", NEW)
        with open(path, "rb") as f:
            first = f.read()
        ids = [r["id"] for r in self.read(path)]
        self.assertEqual(ids, sorted(ids))
        snapshot.process(d, force=True)
        with open(path, "rb") as f:
            self.assertEqual(first, f.read())
        self.assertEqual(first[4:8], b"\0\0\0\0")  # gzip mtime field

    def test_snapshot_no_overwrite_without_force(self):
        d, path = self.make("p", OLD)
        with open(path, "wb") as f:
            f.write(b"sentinel")
        s = snapshot.process(d)
        self.assertFalse(s["written"])
        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"sentinel")
        s = snapshot.process(d, force=True)
        self.assertTrue(s["written"])
        self.assertEqual(len(self.read(path)), 4)

    def test_diff_added_deleted_changed(self):
        rows = {r["id"]: r for r in self.diff_rows()}
        self.assertEqual(rows["f6"]["change"], "added")
        self.assertEqual(rows["c3"]["change"], "deleted")
        self.assertEqual(rows["b2"]["change"], "changed")
        self.assertEqual(rows["b2"]["old_metadata_modified"], "2020-02-01T00:00:00")
        self.assertEqual(rows["b2"]["new_metadata_modified"], "2020-06-01T00:00:00")
        self.assertEqual(rows["b2"]["fields_changed"].split(";"),
                         ["title", "metadata_modified", "num_resources", "resources"])
        self.assertEqual(rows["d4"]["change"], "changed")

    def test_diff_resource_changes(self):
        rows = {r["id"]: r for r in self.diff_rows()}
        b = rows["b2"]
        self.assertEqual((b["resources_added"], b["resources_removed"], b["resources_changed"]),
                         ("0", "1", "1"))
        d = rows["d4"]
        self.assertEqual((d["resources_added"], d["resources_removed"], d["resources_changed"]),
                         ("1", "0", "0"))

    def test_diff_unchanged_not_listed(self):
        rows = self.diff_rows()
        self.assertNotIn("a1", [r["id"] for r in rows])
        self.assertEqual(len(rows), 4)


if __name__ == "__main__":
    unittest.main()
