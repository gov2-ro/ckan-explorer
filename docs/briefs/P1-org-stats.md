# Brief — P1 org stats (for Sonnet)

Read first: `CLAUDE.md`, `docs/BACKLOG.md`, `docs/ACTIVITY.md`, and the spec `docs/specs/P1-org-stats.md`. The spec is the contract. This brief tells you how to deliver it.

## You may create or change

- `org-stats.py` (repo root, next to the other scripts).
- `tests/test_org_stats.py` and `tests/fixtures/*.jsonl`.
- `data/<host>/stats/` (output; do not commit it).
- `docs/ACTIVITY.md`, `docs/BACKLOG.md`, `docs/RELEASES.md`, `readme.md` (one line under Scripts).

## You must not change

- `fetch-datasets.py`, `list-packages.py`, `get-stats.py`, and any `datasets.jsonl` or `package-stats.csv`. Another session owns the ingest work.
- The spec. If the spec is wrong or unclear, stop and ask.

## Steps

1. Write `org-stats.py` to the spec. Use the standard library only. Read `datasets.jsonl` line by line. Match the style of `fetch-datasets.py` (module docstring with usage, `argparse`, `main()`).
2. Write the fixture `tests/fixtures/mini.jsonl` (about 5 packages). It must cover: a package with no organization, a resource with no `created`, a resource with an invalid `created`, an update (`last_modified` more than 1 day after `created`), uploads on both sides of the 12-month boundary, and a duplicate `id`.
3. Write `tests/test_org_stats.py` with `unittest`. Load the script with `importlib`, because the file name has a hyphen. Use these test names:
   - `test_no_org_grouped_as_none`
   - `test_upload_requires_valid_created`
   - `test_update_counted_after_one_day`
   - `test_window_12m_and_60m_boundaries`
   - `test_duplicate_id_kept_once_and_counted`
   - `test_as_of_from_max_metadata_modified`
   - `test_invariants_hold_on_fixture`
   - `test_output_sorted_and_deterministic` (run twice and compare the bytes)
4. Run the tests: `python3 -m unittest discover tests`.
5. Run `python3 org-stats.py --all`. Today `datasets.jsonl` exists for data.gov.ro, data.humdata.org and africaopendata.org.
6. Check the output against the "Known data issues" table in the spec. The date-check counts in `summary.json` must match it, unless the ingest session fetched the files again.

## Report back (in the final message and in `docs/ACTIVITY.md`)

- The test result (output of the test run).
- Per portal: datasets, resources, uploads, updates, orgs, no-org datasets, as-of date, run time, peak memory if easy to get (`/usr/bin/time -l`).
- Per portal: the top 10 organizations by `uploads`, and by `uploads_12m`.
- Anything you assumed. Say what you measured and what you assumed.

## Finish

- In `docs/BACKLOG.md`, set P1 to `[x]`. Add any defects that you found.
- Commit only the files in "You may create or change", but not `data/`. End the commit message with the attribution line from the session.
- This is a user capability, so bump the minor version: add a line to `docs/RELEASES.md` and tag the commit. Run `git tag` first to get the latest version.

## Stop and ask when

- A step would change the spec, an invariant, or a file outside the list above.
- An invariant fails on real data and the cause is not a bug in your code.
- A run takes more than 10 minutes or uses more than 4 GB of memory.
