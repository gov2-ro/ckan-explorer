# Brief — P4 portal registry (for Sonnet)

Read first: `CLAUDE.md` and the spec `docs/specs/P4-portal-registry.md`. The spec is the contract.

## You may create or change

- `portal-probe.py` (repo root).
- `tests/test_portal_probe.py` (no network in tests: use a local `http.server` on 127.0.0.1 in a thread, or mock `urllib`).
- `docs/reference/portal-probe.csv` (output).

## Steps

1. Write `portal-probe.py` to the spec.
2. Tests (names):
   - `test_ok_portal` (status_show and package_search work)
   - `test_no_search`
   - `test_not_ckan_html_answer`
   - `test_fallback_to_host_root_on_404`
   - `test_http_error_no_retry_on_4xx`
   - `test_output_sorted`
3. Run the probe once on the full list (526 URLs). The calls are read-only GETs to public APIs; keep the 8-request limit. Report the run time, the count per status, and the size bands.
4. List in the report the 20 largest `ok` portals (host, datasets, CKAN version), and every `ok` portal with a host in .ro, .md, or another EU country code.

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
