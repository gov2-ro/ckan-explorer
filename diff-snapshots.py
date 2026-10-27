"""
List what changed between two snapshots: added, deleted and changed datasets.

Usage:
    python diff-snapshots.py OLD.jsonl.gz NEW.jsonl.gz [--out FILE.csv]
    python diff-snapshots.py data/data.gov.ro      # the two latest snapshots

Default --out: <dir>/snapshots/diff-<old-as-of>_<new-as-of>.csv
CSV columns: change, id, name, org_name, title, old_metadata_modified,
new_metadata_modified, resources_added, resources_removed, resources_changed,
fields_changed.
`change` is added, deleted or changed. Datasets with no difference are not listed.
Resources are matched by id; a resource is changed if last_modified, format or url differs.
fields_changed lists the slim top-level fields that differ, separated by ";"
("resources" appears when a resource was added, removed or changed).
Stdout: one line with the counts per change type.
Spec: docs/specs/P3-snapshots.md. Standard library only.
"""
import argparse
import csv
import gzip
import json
import os
import re
import sys

COLUMNS = ["change", "id", "name", "org_name", "title", "old_metadata_modified",
           "new_metadata_modified", "resources_added", "resources_removed",
           "resources_changed", "fields_changed"]
FIELDS = ["name", "title", "org_name", "metadata_created", "metadata_modified", "num_resources"]
RES_FIELDS = ["last_modified", "format", "url"]
SNAP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.jsonl\.gz$")
ORDER = {"added": 0, "deleted": 1, "changed": 2}


def load(path):
    """Read a snapshot into a dict id -> record."""
    records = {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                records[rec.get("id")] = rec
    return records


def res_map(rec):
    return {(r.get("id") if r.get("id") is not None else "#%d" % i): r
            for i, r in enumerate(rec.get("resources") or [])}


def compare(old, new):
    """Return (added, removed, changed resource counts, changed field names) for two records."""
    o, n = res_map(old), res_map(new)
    added = len(n.keys() - o.keys())
    removed = len(o.keys() - n.keys())
    changed = sum(1 for k in o.keys() & n.keys() if any(o[k].get(f) != n[k].get(f) for f in RES_FIELDS))
    fields = [f for f in FIELDS if old.get(f) != new.get(f)]
    if added or removed or changed:
        fields.append("resources")
    return added, removed, changed, fields


def diff(old, new):
    """Return CSV rows (lists) for all differences, sorted by change type then id."""
    rows = []
    for pid, rec in new.items():
        if pid not in old:
            rows.append(["added", pid, rec.get("name"), rec.get("org_name"), rec.get("title"),
                         "", rec.get("metadata_modified"), len(rec.get("resources") or []), 0, 0, ""])
            continue
        o = old[pid]
        a, r, c, fields = compare(o, rec)
        if fields:
            rows.append(["changed", pid, rec.get("name"), rec.get("org_name"), rec.get("title"),
                         o.get("metadata_modified"), rec.get("metadata_modified"), a, r, c,
                         ";".join(fields)])
    for pid, rec in old.items():
        if pid not in new:
            rows.append(["deleted", pid, rec.get("name"), rec.get("org_name"), rec.get("title"),
                         rec.get("metadata_modified"), "", 0, len(rec.get("resources") or []), 0, ""])
    rows.sort(key=lambda r: (ORDER[r[0]], str(r[1])))
    return rows


def as_of(path):
    m = SNAP_RE.match(os.path.basename(path))
    return m.group(1) if m else os.path.basename(path).split(".")[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="OLD.jsonl.gz NEW.jsonl.gz, or one portal directory")
    ap.add_argument("--out", metavar="FILE.csv", help="output CSV path")
    args = ap.parse_args()
    if len(args.paths) == 1 and os.path.isdir(args.paths[0]):
        snap_dir = os.path.join(args.paths[0], "snapshots")
        names = sorted(n for n in os.listdir(snap_dir) if SNAP_RE.match(n)) if os.path.isdir(snap_dir) else []
        if len(names) < 2:
            ap.error(f"{snap_dir}: need at least two snapshots")
        old_path, new_path = (os.path.join(snap_dir, n) for n in names[-2:])
    elif len(args.paths) == 2:
        old_path, new_path = args.paths
    else:
        ap.error("give OLD NEW, or one portal directory")
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(new_path)),
                                   f"diff-{as_of(old_path)}_{as_of(new_path)}.csv")
    rows = diff(load(old_path), load(new_path))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)
    counts = {k: sum(1 for r in rows if r[0] == k) for k in ORDER}
    print(f"added={counts['added']} deleted={counts['deleted']} changed={counts['changed']} -> {out}")


if __name__ == "__main__":
    sys.exit(main())
