# Brief — P3 snapshots and diff (for Sonnet)

Read first: `CLAUDE.md` and the spec `docs/specs/P3-snapshots.md`. The spec is the contract. Storage and schedule are not part of this work.

## You may create or change

- `snapshot.py`, `diff-snapshots.py` (repo root).
- `tests/test_snapshots.py`, `tests/fixtures/snap-old.jsonl`, `tests/fixtures/snap-new.jsonl`.
- `data/<host>/snapshots/` (output; never committed in this round).

## Steps

1. Write both scripts to the spec. Read `datasets.jsonl` line by line (HDX is 965 MB).
2. Fixtures: two small files that cover an added, a deleted and a changed dataset; a resource added, removed and changed; and a dataset with no difference.
3. Tests (names):
   - `test_snapshot_slim_fields_only`
   - `test_snapshot_sorted_and_deterministic` (same bytes twice, gzip `mtime=0`)
   - `test_snapshot_no_overwrite_without_force`
   - `test_diff_added_deleted_changed`
   - `test_diff_resource_changes`
   - `test_diff_unchanged_not_listed`
4. Run `snapshot.py --all` on the real data. Report per portal: datasets, snapshot size in bytes, run time, peak memory (`/usr/bin/time -l`).
5. There is only one real snapshot per portal now. To test the diff on real data, make a second snapshot from a copy of data.gov.ro's `datasets.jsonl` in a scratch directory where you delete 3 lines and change 2. Do not change the real file. Report the diff counts.

## Rules for this round (parallel builders)

Three Sonnet agents build P2, P3 and P4 at the same time in the same working tree. To avoid conflicts:

- Do **not** commit, tag, or stage anything. Opus reviews and commits.
- Do **not** edit `docs/ACTIVITY.md`, `docs/BACKLOG.md`, `docs/RELEASES.md`, `readme.md`, `CLAUDE.md`, or any spec. Put what you would write there into your report.
- Do not edit `fetch-datasets.py`, `list-packages.py`, `get-stats.py`, `org-stats.py`, or any `datasets.jsonl` / `package-stats.csv` / `stats/` file.
- Python standard library only. Match the style of `org-stats.py` (module docstring with usage, `argparse`, `main()`).
- Tests: `unittest` in `tests/`, loaded with `importlib` (file names have hyphens). Run all tests with `python3 -m unittest discover tests` before you report.
- Stop and ask (end your work and report) when a step would change the spec, or a run takes more than 15 minutes or 4 GB of memory.

## Report back

- The test output.
- What you ran and what you measured (numbers, run times, file sizes).
- What you assumed. Keep measured and assumed apart.
- The text for `docs/ACTIVITY.md` (Done / Hard / Decided) and any `docs/BACKLOG.md` items.
- The list of files you created or changed.
