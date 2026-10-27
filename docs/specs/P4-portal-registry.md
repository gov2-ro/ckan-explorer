# P4 — Portal registry (spec)

Status: accepted, 2026-10-27. Owner of changes: Opus. Input: `docs/reference/ckan-instances.csv` (526 URLs).

## Goal

Find which candidate portals have a working CKAN API, and how large they are. The result is the basis for the user's rule for which portals to add.

## Probe

`portal-probe.py [--in docs/reference/ckan-instances.csv] [--out docs/reference/portal-probe.csv]`:

For each URL in the input:

1. Call `{url}/api/3/action/status_show`. If it gives `success: true`, record `ckan_version` and `site_url`.
2. Call `{url}/api/3/action/package_search?rows=0`. If it gives `success: true`, record `result.count` as `datasets`.
3. If both calls fail with HTTP 404 and the URL has a path, try again once with the host root (`https://<host>`). Record the URL that worked as `api_base`.

Rules:

- Timeout 20 s per request; 1 retry on a timeout or a 5xx answer; no retry on 4xx.
- At most 8 requests at the same time. User-Agent `ckan-explorer/1.0 (+https://github.com/gov2-ro/ckan-explorer)`.
- HTTPS certificate errors: record them as `tls_error`. Do not turn off verification.
- Follow redirects; record the final host if it differs.

## Output

`docs/reference/portal-probe.csv`, sorted by `host`, then `url`. Columns:

`host, url, api_base, status, http_status, ckan_version, datasets, final_host, error, checked_on`

`status` is one of:

| Value | Meaning |
|---|---|
| `ok` | `package_search` works. |
| `no_search` | `status_show` works, `package_search` does not. |
| `not_ckan` | The host answers, but no CKAN API answer (HTML, 404, or JSON without `success`). |
| `http_error` | 4xx or 5xx after the retry. |
| `timeout` | No answer within the timeout, after the retry. |
| `dns_error` | The host does not resolve. |
| `tls_error` | Certificate or TLS failure. |
| `conn_error` | Any other connection failure. |

`checked_on` is the date of the run (`YYYY-MM-DD`). This is the only output that uses the clock.

Stdout at the end: the count per `status`, and the count of `ok` portals in size bands: < 100, 100–999, 1000–9999, 10000–99999, ≥ 100000 datasets.

## Interface

Python standard library only (`urllib`, `concurrent.futures`).

## Out of scope

- Choosing which portals to add (user decision after the probe).
- Fetching datasets from new portals (ingest work).
