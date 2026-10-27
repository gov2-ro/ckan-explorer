# Brief — P3b weekly snapshot workflow (for Sonnet)

**Start only when `fetch-datasets.py` is committed on `main`.** Until then, this brief is blocked.

Read first: `CLAUDE.md`, the spec `docs/specs/P3b-snapshot-schedule.md`, and `docs/specs/P3-snapshots.md`.

## You may create or change

- `.github/workflows/weekly-snapshot.yml`.
- A helper script if the YAML gets long, for example `ci/weekly-snapshot.sh` or `ci/weekly_snapshot.py` (standard library only).

## Steps

1. Write the workflow to the spec.
2. Check it locally: run the helper script on 2 small portals (data.primariatm.ro, data.gov.lv) with a fake release step (write the assets to a local directory). Report the files and the `run-summary.json`.
3. Do not push. Opus reviews, commits and pushes, and then starts the first run with `workflow_dispatch`.

## Report back

The test output, the local run result, what you assumed, and the text for `docs/ACTIVITY.md` and `docs/BACKLOG.md`. Do not commit; do not edit process files.
