# P8 — Fetch resource fields (spec)

Status: draft, 2026-10-27. Input: `data/<host>/datasets.jsonl`. Output feeds P7.

## Goal

For each resource that is in the CKAN DataStore, record its fields (column names and types) and its row count. The script fetches no rows.

## Prior art (checked 2026-10-27)

No tool found that does this for a whole portal. `ckanapi dump` and `fetch-datasets.py` give package and resource metadata only; neither gives DataStore fields. Hence this script. The method: `datastore_search?resource_id=<id>&limit=0` returns `fields` and `total` and no rows. (Source: CKAN DataStore API; `ckan_datastore_search` description of the ondata MCP server.)

## Interface

```sh
python fetch-fields.py <ckan_instance_url> [--data DIR] [--sleep SECONDS] [--limit N]
```

- Default `--data`: `data/<hostname>/`. The script reads `<DIR>/datasets.jsonl` and writes `<DIR>/fields.jsonl`.
- `--sleep`: pause between requests; default 0.2.
- `--limit`: stop after N requests (for a test run).
- Standard library plus `requests` and `tqdm` (as `fetch-datasets.py`).

## Which resources

A resource qualifies when `datastore_active` is true. The script skips the others and writes no record for them.

## Output record

One JSON line per qualifying resource:

```
{"resource_id": "...", "package_id": "...", "status": "ok",
 "fields": [{"id": "col", "type": "text"}, ...], "total": 123}
```

- `status` is `ok`, `not_found` (HTTP 404 or CKAN error "not found"), `forbidden` (401 or 403), or `error` (other failure after retries; include `"error": "<text>"`).
- The field `_id` that CKAN adds is left out.
- For `ok`, `fields` and `total` are present. For the other statuses they are absent.

## Behavior

- **Resume:** records already in `fields.jsonl` with status `ok`, `not_found` or `forbidden` are kept and skipped. `error` records are fetched again. The script appends each record and flushes at once, so a stop loses no finished work.
- **Retry:** as `fetch-datasets.py` (4 tries, backoff). HTTP 429 and 5xx retry; other 4xx do not and give a status as above.
- **Fail fast:** if the first 20 requests all fail with `error`, stop and print the reason (the portal probably has no DataStore API).
- **Report:** at the end, print resources that qualify, fetched now, already done, and counts by status.
- User agent: `ckan-explorer/1.0`.

## Out of scope

Resources not in the DataStore (files need download and parsing: that is fetching data), HDX by default (about 190,000 resources; run it only on purpose), and merging into the page (P7 does that).
