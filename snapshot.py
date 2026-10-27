"""
Write a slim, dated, reproducible snapshot of each portal's datasets.jsonl.

Usage:
    python snapshot.py data/data.gov.ro [data/data.humdata.org ...]
    python snapshot.py --all                  # every data/*/ with datasets.jsonl
    python snapshot.py data/data.gov.ro --force

Reads <dir>/datasets.jsonl line by line. Writes <dir>/snapshots/<as-of>.jsonl.gz.
The as-of date is the latest metadata_modified in the file (not the clock).
One JSON object per dataset, sorted by id, with only the slim fields:
    id, name, title, org_name, metadata_created, metadata_modified,
    num_resources, resources=[{id, created, last_modified, format, url}]
gzip uses mtime=0, so the same input gives the same bytes.
An existing target file is not overwritten (message, then continue) unless --force.
Spec: docs/specs/P3-snapshots.md. Standard library only.
"""
import argparse
import glob
import gzip
import json
import os
import re
import sys
import time

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
RESOURCE_FIELDS = (("id", "id"), ("created", "created"), ("last_modified", "last_modified"),
                   ("format", "format"), ("url", "url"))


def slim(pkg):
    """Return the slim record for one dataset dict."""
    org = pkg.get("organization") or {}
    resources = [{out: r.get(src) for out, src in RESOURCE_FIELDS}
                 for r in (pkg.get("resources") or []) if isinstance(r, dict)]
    return {
        "id": pkg.get("id"),
        "name": pkg.get("name"),
        "title": pkg.get("title"),
        "org_name": org.get("name") if isinstance(org, dict) else None,
        "metadata_created": pkg.get("metadata_created"),
        "metadata_modified": pkg.get("metadata_modified"),
        "num_resources": pkg.get("num_resources"),
        "resources": resources,
    }


def read_slim(path):
    """Read datasets.jsonl line by line. Return (records by id, latest date, duplicates)."""
    records = {}
    latest = None
    dups = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pkg = json.loads(line)
            md = pkg.get("metadata_modified")
            if isinstance(md, str) and DATE_RE.match(md):
                if latest is None or md[:19] > latest:
                    latest = md[:19]
            pid = pkg.get("id")
            if pid in records:
                dups += 1
                continue
            records[pid] = slim(pkg)
    return records, latest[:10] if latest else None, dups


def write_snapshot(records, target):
    """Write records sorted by id as deterministic gzip JSON lines."""
    tmp = target + ".tmp"
    with open(tmp, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0) as gz:
            for pid in sorted(records, key=lambda k: (k is None, str(k))):
                line = json.dumps(records[pid], ensure_ascii=False, separators=(",", ":"))
                gz.write(line.encode("utf-8") + b"\n")
    os.replace(tmp, target)


def process(portal_dir, force=False):
    src = os.path.join(portal_dir, "datasets.jsonl")
    records, as_of, dups = read_slim(src)
    if as_of is None:
        raise SystemExit(f"{src}: no valid metadata_modified")
    out_dir = os.path.join(portal_dir, "snapshots")
    target = os.path.join(out_dir, as_of + ".jsonl.gz")
    result = {"portal": os.path.basename(os.path.normpath(portal_dir)), "datasets": len(records),
              "duplicate_ids": dups, "as_of": as_of, "path": target, "written": False, "bytes": None}
    if os.path.exists(target) and not force:
        print(f"{target}: exists, not overwritten (use --force)")
        result["bytes"] = os.path.getsize(target)
        return result
    os.makedirs(out_dir, exist_ok=True)
    write_snapshot(records, target)
    result["written"] = True
    result["bytes"] = os.path.getsize(target)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="*", help="portal directories, e.g. data/data.gov.ro")
    ap.add_argument("--all", action="store_true", help="every data/*/ with datasets.jsonl")
    ap.add_argument("--force", action="store_true", help="overwrite an existing snapshot")
    args = ap.parse_args()
    dirs = list(args.dirs)
    if args.all:
        here = os.path.dirname(os.path.abspath(__file__))
        dirs += sorted(os.path.dirname(p) for p in glob.glob(os.path.join(here, "data", "*", "datasets.jsonl")))
    if not dirs:
        ap.error("give portal directories or --all")
    for pd in dirs:
        t0 = time.time()
        s = process(pd, args.force)
        state = "written" if s["written"] else "kept"
        print(f"{s['portal']}: datasets={s['datasets']} as_of={s['as_of']} bytes={s['bytes']} "
              f"{state} duplicate_ids={s['duplicate_ids']} time={time.time() - t0:.1f}s")


if __name__ == "__main__":
    sys.exit(main())
