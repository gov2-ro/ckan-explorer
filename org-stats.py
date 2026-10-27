"""
Compute publishing activity per organization and per dataset from datasets.jsonl.

Usage:
    python org-stats.py data/data.gov.ro [data/data.humdata.org ...]
    python org-stats.py --all                      # every data/*/ with datasets.jsonl
    python org-stats.py data/data.gov.ro --as-of 2026-10-01

Reads <dir>/datasets.jsonl line by line. Writes (overwriting) to <dir>/stats/:
    orgs.csv, org-monthly.csv, datasets.csv, summary.json

Main metric: uploads = resources with a valid `created` date (period = month of
`created`). Secondary: updates = resources whose `last_modified` is more than
1 day after `created` (period = month of `last_modified`).
The as-of date is the latest metadata_modified in the file (not the clock).
Spec: docs/specs/P1-org-stats.md. Standard library only.
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

NO_ORG_NAME = "_none"
NO_ORG_TITLE = "(no organization)"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
ONE_DAY = timedelta(days=1)

ORG_COLS = ["org_name", "org_title", "datasets", "resources", "uploads", "updates",
            "first_upload", "last_upload", "uploads_12m", "uploads_60m",
            "datasets_12m", "active_months"]
MONTHLY_COLS = ["org_name", "month", "uploads", "updates", "datasets"]
DATASET_COLS = ["id", "name", "title", "org_name", "resources", "uploads", "updates",
                "first_upload", "last_upload", "timespan_days", "active_months",
                "metadata_created", "metadata_modified"]


def parse_date(value):
    """Return a datetime for a valid ISO timestamp (first 19 chars), else None."""
    if not isinstance(value, str) or not DATE_RE.match(value):
        return None
    try:
        return datetime.strptime(value[:10] + "T" + value[11:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def month_index(dt):
    return dt.year * 12 + dt.month - 1


def month_label(idx):
    return "%04d-%02d" % (idx // 12, idx % 12 + 1)


def read_datasets(path):
    """Scan the file once. Return (datasets, summary counters)."""
    datasets = {}
    c = Counter()
    created_min = created_max = None
    max_modified = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pkg = json.loads(line)
            md = parse_date(pkg.get("metadata_modified"))
            if md is not None and (max_modified is None or md > max_modified):
                max_modified = md
            pid = pkg.get("id")
            if pid in datasets:
                c["duplicate_ids"] += 1
                continue
            org = pkg.get("organization") or {}
            org_name = org.get("name") or NO_ORG_NAME
            org_title = (org.get("title") or org_name) if org.get("name") else NO_ORG_TITLE
            if org_name == NO_ORG_NAME:
                c["no_org_datasets"] += 1
            ds = {"id": pid, "name": pkg.get("name") or "", "title": pkg.get("title") or "",
                  "org_name": org_name, "org_title": org_title,
                  "metadata_created": pkg.get("metadata_created") or "",
                  "metadata_modified": pkg.get("metadata_modified") or "",
                  "resources": 0, "up": Counter(), "upd": Counter(),
                  "first": None, "last": None}
            for r in pkg.get("resources") or []:
                ds["resources"] += 1
                c["resources"] += 1
                cr = parse_date(r.get("created"))
                lm = parse_date(r.get("last_modified"))
                if cr is None:
                    c["resources_invalid_created" if r.get("created") else "resources_no_created"] += 1
                else:
                    ds["up"][month_index(cr)] += 1
                    c["uploads"] += 1
                    if ds["first"] is None or cr < ds["first"]:
                        ds["first"] = cr
                    if ds["last"] is None or cr > ds["last"]:
                        ds["last"] = cr
                    if created_min is None or cr < created_min:
                        created_min = cr
                    if created_max is None or cr > created_max:
                        created_max = cr
                if not r.get("last_modified"):
                    c["resources_no_last_modified"] += 1
                if cr is not None and lm is not None:
                    if lm > cr + ONE_DAY:
                        ds["upd"][month_index(lm)] += 1
                        c["last_modified_after_created_1d"] += 1
                    elif lm < cr - ONE_DAY:
                        c["last_modified_before_created_1d"] += 1
            datasets[pid] = ds
    c["created_min"] = created_min.isoformat() if created_min else None
    c["created_max"] = created_max.isoformat() if created_max else None
    return datasets, c, max_modified


def d(dt):
    return dt.strftime("%Y-%m-%d") if dt else ""


def compute(datasets, as_of):
    """Return (orgs rows, monthly rows, dataset rows) as lists of lists."""
    as_idx = month_index(as_of)
    lo12, lo60 = as_idx - 11, as_idx - 59
    orgs = {}
    monthly = {}
    ds_rows = []
    for ds in datasets.values():
        up, upd = ds["up"], ds["upd"]
        n_up, n_upd = sum(up.values()), sum(upd.values())
        o = orgs.setdefault(ds["org_name"], {
            "title": ds["org_title"], "datasets": 0, "resources": 0, "uploads": 0,
            "updates": 0, "first": None, "last": None, "u12": 0, "u60": 0,
            "d12": 0, "months": set()})
        o["datasets"] += 1
        o["resources"] += ds["resources"]
        o["uploads"] += n_up
        o["updates"] += n_upd
        if ds["first"] and (o["first"] is None or ds["first"] < o["first"]):
            o["first"] = ds["first"]
        if ds["last"] and (o["last"] is None or ds["last"] > o["last"]):
            o["last"] = ds["last"]
        in12 = 0
        for m, n in up.items():
            if lo12 <= m <= as_idx:
                o["u12"] += n
                in12 += n
            if lo60 <= m <= as_idx:
                o["u60"] += n
            o["months"].add(m)
            monthly.setdefault((ds["org_name"], m), [0, 0, 0])[0] += n
            monthly[(ds["org_name"], m)][2] += 1
        if in12:
            o["d12"] += 1
        for m, n in upd.items():
            monthly.setdefault((ds["org_name"], m), [0, 0, 0])[1] += n
        span = (ds["last"].date() - ds["first"].date()).days if ds["first"] else ""
        ds_rows.append([ds["id"], ds["name"], ds["title"], ds["org_name"], ds["resources"],
                        n_up, n_upd, d(ds["first"]), d(ds["last"]), span, len(up),
                        ds["metadata_created"], ds["metadata_modified"]])
    org_rows = [[k, o["title"], o["datasets"], o["resources"], o["uploads"], o["updates"],
                 d(o["first"]), d(o["last"]), o["u12"], o["u60"], o["d12"], len(o["months"])]
                for k, o in orgs.items()]
    org_rows.sort(key=lambda r: (-r[4], r[0]))
    mon_rows = [[k[0], month_label(k[1]), v[0], v[1], v[2]] for k, v in monthly.items()]
    mon_rows.sort(key=lambda r: (r[0], r[1]))
    ds_rows.sort(key=lambda r: r[0])
    return org_rows, mon_rows, ds_rows


def check_invariants(org_rows, mon_rows, counts, n_datasets):
    inv = {
        "orgs_datasets_sum_equals_datasets": sum(r[2] for r in org_rows) == n_datasets,
        "orgs_resources_sum_equals_resources": sum(r[3] for r in org_rows) == counts["resources"],
        "monthly_uploads_equals_orgs_uploads_equals_valid_created":
            sum(r[2] for r in mon_rows) == sum(r[4] for r in org_rows) == counts["uploads"],
        "per_org_12m_le_60m_le_all": all(r[8] <= r[9] <= r[4] for r in org_rows),
    }
    return inv


def write_csv(path, cols, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        w.writerows(rows)


def process(portal_dir, as_of_override=None):
    src = os.path.join(portal_dir, "datasets.jsonl")
    datasets, c, max_modified = read_datasets(src)
    if as_of_override:
        as_of = datetime.strptime(as_of_override, "%Y-%m-%d")
    elif max_modified:
        as_of = max_modified
    else:
        raise SystemExit(f"{src}: no valid metadata_modified; give --as-of")
    org_rows, mon_rows, ds_rows = compute(datasets, as_of)
    inv = check_invariants(org_rows, mon_rows, c, len(datasets))
    st = os.stat(src)
    summary = {
        "portal": os.path.basename(os.path.normpath(portal_dir)),
        "source": {"path": src, "size_bytes": st.st_size,
                   "modified": datetime.fromtimestamp(st.st_mtime, timezone.utc)
                   .strftime("%Y-%m-%dT%H:%M:%SZ")},
        "as_of": d(as_of),
        "datasets": len(datasets),
        "duplicate_ids": c["duplicate_ids"],
        "resources": c["resources"],
        "uploads": c["uploads"],
        "updates": c["last_modified_after_created_1d"],
        "orgs": sum(1 for r in org_rows if r[0] != NO_ORG_NAME),
        "no_org_datasets": c["no_org_datasets"],
        "resources_no_created": c["resources_no_created"],
        "resources_invalid_created": c["resources_invalid_created"],
        "resources_no_last_modified": c["resources_no_last_modified"],
        "last_modified_after_created_1d": c["last_modified_after_created_1d"],
        "last_modified_before_created_1d": c["last_modified_before_created_1d"],
        "created_min": c["created_min"],
        "created_max": c["created_max"],
        "invariants": inv,
    }
    out = os.path.join(portal_dir, "stats")
    os.makedirs(out, exist_ok=True)
    write_csv(os.path.join(out, "orgs.csv"), ORG_COLS, org_rows)
    write_csv(os.path.join(out, "org-monthly.csv"), MONTHLY_COLS, mon_rows)
    write_csv(os.path.join(out, "datasets.csv"), DATASET_COLS, ds_rows)
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    failed = [k for k, v in inv.items() if not v]
    if failed:
        raise SystemExit(f"{portal_dir}: invariant failed: {', '.join(failed)}")
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="*", help="portal directories, e.g. data/data.gov.ro")
    ap.add_argument("--all", action="store_true", help="every data/*/ with datasets.jsonl")
    ap.add_argument("--as-of", metavar="YYYY-MM-DD", help="override the as-of date")
    args = ap.parse_args()
    dirs = list(args.dirs)
    if args.all:
        here = os.path.dirname(os.path.abspath(__file__))
        dirs += sorted(os.path.dirname(p) for p in glob.glob(os.path.join(here, "data", "*", "datasets.jsonl")))
    if not dirs:
        ap.error("give portal directories or --all")
    for pd in dirs:
        t0 = time.time()
        s = process(pd, args.as_of)
        print(f"{s['portal']}: datasets={s['datasets']} resources={s['resources']} "
              f"uploads={s['uploads']} orgs={s['orgs']} time={time.time() - t0:.1f}s")


if __name__ == "__main__":
    sys.exit(main())
