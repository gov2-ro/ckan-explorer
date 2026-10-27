"""
Fetch all dataset metadata from a CKAN portal by paging through package_search.

Usage:
    python fetch-datasets.py <ckan_instance_url> [--out DIR]

Default out dir is data/<hostname>/ . Writes (overwriting):
    package-stats.csv  (with header)
    datasets.jsonl     (raw package dicts, one per line)

Known portals (for reference):
    https://data.gov.ro
    https://data.gov.md/ckan
    https://data.humdata.org/
    https://catalog.data.gov/      (300k+ datasets, very slow)
    https://data.gov.sg
    https://africaopendata.org/
    https://katalog.data.go.id/
    https://datastore.brussels/
"""
import argparse
import csv
import json
import os
import sys
from time import sleep
from urllib.parse import urlparse

import requests
from tqdm import tqdm

ROWS = 1000
RETRIES = 4
PAGE_SLEEP = 0.5

COLUMNS = ["id", "metadata_created", "metadata_modified", "num_resources",
           "name", "title", "org", "org_name", "org_title"]


def fetch_page(session, base, start):
    params = {"q": "*:*", "rows": ROWS, "start": start, "sort": "id asc"}
    url = f"{base}/api/3/action/package_search"
    last = None
    for attempt in range(RETRIES):
        try:
            r = session.get(url, params=params, timeout=120)
            if 400 <= r.status_code < 500 and r.status_code != 429:
                raise SystemExit(f"HTTP {r.status_code} for {r.url} (not a CKAN API endpoint?)")
            r.raise_for_status()
            j = r.json()
            if not j.get("success"):
                raise RuntimeError(f"API error: {j.get('error')}")
            return j["result"]
        except Exception as e:  # retry on any failure
            last = e
            wait = 2 ** (attempt + 1)
            tqdm.write(f"  [retry {attempt + 1}/{RETRIES}] start={start}: {e} (sleep {wait}s)")
            sleep(wait)
    raise SystemExit(f"Giving up at start={start}: {last}")


def to_row(p):
    org = p.get("organization") or {}
    return {
        "id": p.get("id", ""),
        "metadata_created": p.get("metadata_created", ""),
        "metadata_modified": p.get("metadata_modified", ""),
        "num_resources": p.get("num_resources", ""),
        "name": p.get("name", ""),
        "title": p.get("title", ""),
        "org": json.dumps(org, ensure_ascii=False) if org else "",
        "org_name": org.get("name") or "",
        "org_title": org.get("title") or "",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("url", help="CKAN instance URL, e.g. https://data.gov.md/ckan")
    ap.add_argument("--out", help="output dir (default data/<hostname>/)")
    args = ap.parse_args()

    base = args.url.strip().rstrip("/")
    out = args.out or os.path.join("data", urlparse(base).hostname)
    os.makedirs(out, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "ckan-explorer/1.0"

    seen = {}
    start = 0
    count = None
    pbar = None
    while True:
        res = fetch_page(session, base, start)
        count = res.get("count", 0)
        results = res.get("results", [])
        if pbar is None:
            print(f"Portal reports {count} datasets")
            pbar = tqdm(total=count)
        if not results:
            break
        for p in results:
            seen.setdefault(p.get("id"), p)
        start += len(results)
        pbar.update(len(results))
        if start >= count:
            break
        sleep(PAGE_SLEEP)
    if pbar:
        pbar.close()

    with open(os.path.join(out, "datasets.jsonl"), "w", encoding="utf-8") as f:
        for p in seen.values():
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(os.path.join(out, "package-stats.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for p in seen.values():
            w.writerow(to_row(p))

    print(f"Reported count: {count}; rows written: {len(seen)} -> {out}")
    if len(seen) != count:
        print(f"WARNING: rows written ({len(seen)}) != reported count ({count})", file=sys.stderr)


if __name__ == "__main__":
    main()
