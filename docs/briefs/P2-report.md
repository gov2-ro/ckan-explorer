# Brief — P2 report (for Sonnet)

Read first: `CLAUDE.md`, the spec `docs/specs/P2-report.md`, and `docs/specs/P1-org-stats.md` (the input format). The spec is the contract.

## You may create or change

- `report.py` (repo root).
- `tests/test_report.py`, `tests/fixtures/stats-mini/` (a small P1-style stats directory).
- `site/` (output).

## Steps

1. Before you write chart code, load the `dataviz` skill with the Skill tool if it is available, and follow it for the heatmap colors, legend and tooltips. Check the colors in both themes.
2. Write `report.py` to the spec.
3. Tests (names):
   - `test_titles_are_escaped` (a title with `<script>` and `&`)
   - `test_embedded_json_escapes_lt`
   - `test_output_deterministic` (two runs, same bytes)
   - `test_view_rows_union_of_top_by_uploads_and_datasets`
   - `test_windows_end_at_as_of_month`
   - `test_no_external_resources` (no `http` in `src=` or `href=` of `<script>`/`<link>`)
   - `test_hdx_note_present`
4. Run `python3 report.py` on the real `data/*/stats/` (data.gov.ro, data.humdata.org, africaopendata.org). Report the page sizes.
5. Open each page in a headless check if you can (for example, parse it and run a JavaScript syntax check with `node --check` on the extracted script, if node is installed). Say what you could and could not check.

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
