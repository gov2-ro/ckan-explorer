# P3 — Snapshots and diff (spec, local part)

Status: accepted for the local part, 2026-10-27. Storage location and schedule are **not decided** (see "Open decisions"). Owner of changes: Opus.

## Goal

Keep dated copies of each portal's `datasets.jsonl`, and list what changed between two copies: new, deleted and changed datasets. `package_search` does not return deleted datasets, so snapshots are the only way to see deletions.

## Snapshot

`snapshot.py <data/host>...` (or `--all`):

- Reads `data/<host>/datasets.jsonl`.
- Writes `data/<host>/snapshots/<as-of>.jsonl.gz`. The as-of date is the latest `metadata_modified` in the file (same rule as P1).
- Writes a slim form: one JSON object per dataset with only the fields in "Slim record". The full file is too large (HDX: 965 MB).
- Sorted by `id`. gzip with `mtime=0`, so the same input gives the same bytes.
- If the target file exists, the script does not overwrite it. It prints a message and continues. `--force` overwrites.

### Slim record

`id, name, title, org_name, metadata_created, metadata_modified, num_resources`, and `resources`: a list of `{id, created, last_modified, format, url}`.

## Diff

`diff-snapshots.py <old.jsonl.gz> <new.jsonl.gz> [--out FILE.csv]` (or `diff-snapshots.py data/<host>` to compare the two latest snapshots):

- Output CSV columns: `change, id, name, org_name, title, old_metadata_modified, new_metadata_modified, resources_added, resources_removed, resources_changed, fields_changed`.
- `change` is one of `added`, `deleted`, `changed`. Datasets with no difference are not in the output.
- `changed`: `metadata_modified` differs, or a slim field differs. `fields_changed` lists the names of the slim top-level fields that differ, separated by `;`.
- Resources are matched by `id`. A resource is changed if its `last_modified`, `format` or `url` differs.
- Stdout: one line with the counts per change type.
- Default `--out`: `data/<host>/snapshots/diff-<old-as-of>_<new-as-of>.csv`.

## Interface

Python standard library only. The scripts only read `datasets.jsonl`; they do not fetch.

## Open decisions (owner: user)

1. Storage: repo (the slim gzip size decides if this works), GitHub release assets, or other storage.
2. Schedule: how often, and on which machine (GitHub Actions or local cron). The fetch belongs to the ingest work.
3. Retention: keep all snapshots, or thin old ones (for example one per month after a year).

Until these are decided, `data/<host>/snapshots/` is not committed.

## Out of scope

- Fetching (ingest work), scheduling, upload to storage.
- Changes to P1 or P2 output.
