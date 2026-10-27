# P1 — Org stats (spec)

Status: accepted, 2026-10-27. Owner of changes: Opus. Background: `docs/ANALYSIS.md` sections 2, 4 and 9.

## Goal

For each portal, compute publishing activity per organization and per dataset from `datasets.jsonl`. The output feeds the P2 report. The main metric is **uploads per period**.

## Input

- `data/<host>/datasets.jsonl`, written by `fetch-datasets.py` (owned by the ingest work). One raw CKAN package per line.
- The script only reads this file. Files can be large (data.humdata.org: 965 MB), so the script reads them line by line.

## Definitions

| Term | Definition |
|---|---|
| Dataset | One line of `datasets.jsonl`. If an `id` occurs again, keep the first line and count the duplicate in `summary.json`. |
| Organization | `organization.name` of the package. Display name: `organization.title`. |
| No organization | A package with an empty `organization`. Group it as `org_name = _none`, `org_title = (no organization)`. |
| Resource | One item of `resources[]`. |
| Upload | One resource with a valid `created` date. Its period is the month of `created`. |
| Update | One resource whose `last_modified` is more than 1 day after its `created`. Its period is the month of `last_modified`. Secondary metric. |
| Valid date | An ISO timestamp; the script reads the first 19 characters and ignores any time zone. Other values are invalid and are counted in `summary.json`. |
| Month | `YYYY-MM` of a valid date. |
| As-of date | The latest `metadata_modified` in the file. The `--as-of YYYY-MM-DD` option overrides it. The script never uses the clock, so a rerun on the same file gives the same output. |
| Last 12 months | The 12 calendar months that end with the as-of month, inclusive. |
| Last 5 years | The 60 calendar months that end with the as-of month, inclusive. |
| Active month | A month with at least 1 upload. |
| Timespan | Days from the first upload to the last upload of a dataset. |

## Output

The script writes to `data/<host>/stats/` and overwrites the files each run. CSV files are UTF-8, with a header, and in a fixed sort order.

### `orgs.csv` — one row per organization

`org_name, org_title, datasets, resources, uploads, updates, first_upload, last_upload, uploads_12m, uploads_60m, datasets_12m, active_months`

- `first_upload`, `last_upload`: `YYYY-MM-DD`, empty if there are no uploads.
- `datasets_12m`: datasets with at least 1 upload in the last 12 months.
- Sort: `uploads` descending, then `org_name`.

### `org-monthly.csv` — one row per organization and active month

`org_name, month, uploads, updates, datasets`

- `datasets`: datasets with at least 1 upload in that month.
- The file has rows only for months with uploads or updates (long format).
- Sort: `org_name`, then `month`.

### `datasets.csv` — one row per dataset

`id, name, title, org_name, resources, uploads, updates, first_upload, last_upload, timespan_days, active_months, metadata_created, metadata_modified`

- Sort: `id`.

### `summary.json`

- `portal` (the directory name), `source` (path, size in bytes, modification time), `as_of`.
- Counts: `datasets`, `duplicate_ids`, `resources`, `orgs`, `no_org_datasets`.
- Date checks: `resources_no_created`, `resources_invalid_created`, `resources_no_last_modified`, `last_modified_after_created_1d`, `last_modified_before_created_1d`, `created_min`, `created_max`.
- `invariants`: the result of each check below.

## Invariants

The script checks these and exits with an error if one fails:

1. Sum of `orgs.datasets` = `datasets` in the summary.
2. Sum of `orgs.resources` = `resources` in the summary.
3. Sum of `org-monthly.uploads` = sum of `orgs.uploads` = resources with a valid `created`.
4. For each organization: `uploads_12m` ≤ `uploads_60m` ≤ `uploads`.

## Interface

```sh
python org-stats.py data/data.gov.ro [data/data.humdata.org ...]
python org-stats.py --all            # every data/*/ that has datasets.jsonl
python org-stats.py data/data.gov.ro --as-of 2026-10-01
```

- Python standard library only.
- One line per portal on stdout: portal, datasets, resources, uploads, orgs, run time.

## Known data issues (measured 2026-10-27, full files)

| Portal | Resources | `last_modified` > `created` + 1 day | `last_modified` < `created` − 1 day | No organization |
|---|---:|---:|---:|---:|
| data.gov.ro | 39804 | 2033 | 0 | 0 of 5260 |
| data.humdata.org | 191615 | 92995 | 58156 | 0 of 28832 |
| africaopendata.org | 19573 | 1019 | 0 | 1974 of 6982 |

On data.humdata.org, 30% of resources have `last_modified` before `created`. Thus HDX probably resets `created` when a file is replaced, and `created` is not the first upload. P1 does not correct this. P2 must show a note for HDX. A later item can study HDX dates.

## Out of scope

- The report (P2), snapshots (P3), portal checks (P4).
- Changes to `fetch-datasets.py`.
- The legacy `package-stats.csv` files.
