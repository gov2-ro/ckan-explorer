"""
Probe candidate CKAN portals: does the API work, and how many datasets are there?

Usage:
    python portal-probe.py
    python portal-probe.py --in docs/reference/ckan-instances.csv \
                           --out docs/reference/portal-probe.csv

For each URL in the input CSV (column `url`) the script calls, read-only:
    {url}/api/3/action/status_show            -> ckan_version, site_url
    {url}/api/3/action/package_search?rows=0  -> datasets (result.count)
If both calls give HTTP 404 and the URL has a path, it tries once more with the
host root. Timeout 20 s, 1 retry on timeout or 5xx, none on 4xx, at most 8
requests at the same time. TLS verification stays on.

Writes (overwriting) the output CSV, sorted by host then url:
    host,url,api_base,status,http_status,ckan_version,datasets,final_host,error,checked_on
status: ok | no_search | not_ckan | http_error | timeout | dns_error | tls_error | conn_error
checked_on is the date of the run: the only use of the clock in the output.
Spec: docs/specs/P4-portal-registry.md. Standard library only.
"""
import argparse
import csv
import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from urllib.parse import urlsplit

USER_AGENT = "ckan-explorer/1.0 (+https://github.com/gov2-ro/ckan-explorer)"
TIMEOUT = 20
MAX_WORKERS = 8
OUT_COLS = ["host", "url", "api_base", "status", "http_status", "ckan_version",
            "datasets", "final_host", "error", "checked_on"]
STATUSES = ["ok", "no_search", "not_ckan", "http_error", "timeout", "dns_error",
            "tls_error", "conn_error"]
BANDS = [("< 100", 0, 100), ("100-999", 100, 1000), ("1000-9999", 1000, 10000),
         ("10000-99999", 10000, 100000), (">= 100000", 100000, None)]


def classify_exc(exc):
    """Map a network exception to a status value."""
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return "timeout"
    if isinstance(reason, socket.gaierror):
        return "dns_error"
    if isinstance(reason, (ssl.SSLError, ssl.CertificateError)):
        return "tls_error"
    return "conn_error"


def fetch_once(url, timeout):
    """One GET. Returns dict: http (int|None), data (parsed JSON|None),
    final_url, net (network status or None), error (str)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/json"})
    res = {"http": None, "data": None, "final_url": url, "net": None, "error": ""}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            res["http"] = r.status
            res["final_url"] = r.geturl()
            body = r.read()
    except urllib.error.HTTPError as e:
        res["http"] = e.code
        res["final_url"] = e.geturl() or url
        res["error"] = "HTTP %d" % e.code
        e.close()
        return res
    except Exception as e:  # network-level failure
        res["net"] = classify_exc(e)
        res["error"] = "%s: %s" % (type(e).__name__, e)
        return res
    try:
        res["data"] = json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        res["error"] = "not JSON"
    return res


def fetch(url, timeout=TIMEOUT):
    """GET with 1 retry on timeout or 5xx. No retry on 4xx."""
    res = fetch_once(url, timeout)
    if res["net"] == "timeout" or (res["http"] or 0) >= 500:
        res = fetch_once(url, timeout)
    return res


def api_ok(res):
    d = res["data"]
    return res["http"] == 200 and isinstance(d, dict) and d.get("success") is True


def probe_base(base, timeout):
    """Probe one API base. Returns dict with status, http_status, version, datasets, ..."""
    out = {"status": "", "http_status": "", "ckan_version": "", "datasets": "",
           "final_host": "", "error": "", "both_404": False}
    s = fetch(base + "/api/3/action/status_show", timeout)
    out["http_status"] = s["http"] or ""
    out["final_host"] = urlsplit(s["final_url"]).hostname or ""
    if s["net"]:
        # Host is down at network level: a second call would fail the same way.
        out["status"] = s["net"]
        out["error"] = s["error"]
        return out
    show_ok = api_ok(s)
    if show_ok:
        r = s["data"].get("result") or {}
        out["ckan_version"] = r.get("ckan_version", "") if isinstance(r, dict) else ""
    p = fetch(base + "/api/3/action/package_search?rows=0", timeout)
    if p["net"] and not show_ok:
        out["status"] = p["net"]
        out["error"] = p["error"]
        return out
    if api_ok(p):
        r = p["data"].get("result")
        count = r.get("count") if isinstance(r, dict) else None
        if isinstance(count, int):
            out["status"] = "ok"
            out["datasets"] = count
            out["http_status"] = p["http"]
            out["final_host"] = urlsplit(p["final_url"]).hostname or out["final_host"]
            return out
    if show_ok:
        out["status"] = "no_search"
        out["error"] = p["error"] or "package_search failed"
        return out
    codes = (s["http"], p["http"])
    out["both_404"] = codes == (404, 404)
    bad = [c for c in codes if c and c != 404 and c >= 400]
    if bad:
        out["status"] = "http_error"
        out["http_status"] = bad[0]
        out["error"] = "HTTP %d" % bad[0]
    else:
        out["status"] = "not_ckan"
        out["error"] = s["error"] or p["error"] or "no CKAN API answer"
    return out


def probe(url, timeout=TIMEOUT):
    """Probe one input URL. Returns a row dict (without checked_on)."""
    url = url.strip()
    base = url.rstrip("/")
    parts = urlsplit(base)
    res = probe_base(base, timeout)
    api_base = base
    if res["both_404"] and parts.path not in ("", "/"):
        root = "%s://%s" % (parts.scheme, parts.netloc)
        res2 = probe_base(root, timeout)
        if res2["status"] in ("ok", "no_search"):
            res, api_base = res2, root
    row = {"host": parts.hostname or "", "url": url,
           "api_base": api_base if res["status"] in ("ok", "no_search") else "",
           "status": res["status"], "http_status": res["http_status"],
           "ckan_version": res["ckan_version"], "datasets": res["datasets"],
           "final_host": "", "error": res["error"]}
    fh = res["final_host"]
    if fh and fh != row["host"]:
        row["final_host"] = fh
    return row


def read_urls(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [r["url"].strip() for r in csv.DictReader(f) if (r.get("url") or "").strip()]


def run(urls, timeout=TIMEOUT, workers=MAX_WORKERS, today=None):
    today = today or date.today().isoformat()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(lambda u: probe(u, timeout), urls))
    for r in rows:
        r["checked_on"] = today
    rows.sort(key=lambda r: (r["host"], r["url"]))
    return rows


def write_rows(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def summary(rows):
    lines = ["status counts:"]
    for st in STATUSES:
        lines.append("  %-11s %d" % (st, sum(1 for r in rows if r["status"] == st)))
    lines.append("ok portals by size (datasets):")
    sizes = [int(r["datasets"]) for r in rows if r["status"] == "ok"]
    for name, lo, hi in BANDS:
        n = sum(1 for x in sizes if x >= lo and (hi is None or x < hi))
        lines.append("  %-12s %d" % (name, n))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--in", dest="inp", default="docs/reference/ckan-instances.csv")
    ap.add_argument("--out", default="docs/reference/portal-probe.csv")
    args = ap.parse_args()
    urls = read_urls(args.inp)
    t0 = time.time()
    rows = run(urls)
    write_rows(rows, args.out)
    print("probed %d URLs in %.0f s -> %s" % (len(rows), time.time() - t0, args.out))
    print(summary(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
