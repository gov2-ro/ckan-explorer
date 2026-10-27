# P3b — Weekly snapshots on GitHub Actions (spec)

Status: accepted, 2026-10-27. Owner of changes: Opus. Decided by the user: weekly, stored as GitHub release assets.

**Blocked:** `fetch-datasets.py` is not committed yet (ingest work). The workflow needs it in the repo.

## Goal

Every week, fetch each selected portal, make a slim snapshot (P3), make the diff against the previous week, and attach the files to a GitHub release. Snapshots stay out of git history.

## Portal list

`docs/reference/portals-selected.csv`, column `url`, only rows with `active = yes`. The workflow reads this file; there is no second list.

Rule (user, 2026-10-27): during development, portals with 10,000 datasets or more are not active. Change the `active` column to include them later.

## Workflow

`.github/workflows/weekly-snapshot.yml`:

- Triggers: `schedule` (Monday 03:00 UTC) and `workflow_dispatch`.
- `permissions: contents: write`. No other secrets than `GITHUB_TOKEN`.
- Python 3.12; `pip install requests tqdm`.
- One job. Portals run one after the other. For each portal:
  1. `python fetch-datasets.py <url> --out work/<host>`.
  2. `python snapshot.py work/<host>`.
  3. Delete `work/<host>/datasets.jsonl` (disk space; HDX is 965 MB, govdata.de can be larger).
  4. If a portal fails, record it and continue with the next portal.
- Release:
  - Tag and name: `snapshots-<YYYY-MM-DD>` (run date, UTC). The tag points to the commit that the workflow ran on.
  - Assets: `<host>_<as-of>.jsonl.gz` for each portal, `diff_<host>_<old-as-of>_<new-as-of>.csv` for each portal with a previous snapshot, and `run-summary.json` (per portal: status, datasets, as-of, bytes, seconds, error).
  - The previous snapshot comes from the latest earlier `snapshots-*` release (`gh release download`).
- The job fails (red) only if every portal failed. Partial failure is in `run-summary.json`.

## Limits (to check in the first run)

- GitHub job limit is 6 hours. Expected time with the active portals is a few minutes.
- A release asset can be up to 2 GB. Expected sizes are under 50 MB.

## Out of scope

- Changes to `fetch-datasets.py` (ingest work).
- Running P1 stats or P2 report in the workflow (later item).
- Retention or thinning of old releases (later item; about 900 MB a year is expected).
