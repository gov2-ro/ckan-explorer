# Backlog

Statuses: `[ ]` open, `[~]` in progress, `[x]` done, `[-]` dropped.

## Roadmap

- [x] Extract the 2023 notes into `docs/ANALYSIS.md` and `docs/reference/ckan-instances.csv`.
- [x] Set priorities from `docs/ANALYSIS.md` (sections 8 and 9).
- [x] **P1 — Org stats.** Spec: `docs/specs/P1-org-stats.md`. Brief for Sonnet: `docs/briefs/P1-org-stats.md`. Done 2026-10-27: `org-stats.py`, tests in `tests/`. For every working portal, read `datasets.jsonl` and write per-org and per-dataset tables: datasets, resources, uploads per month (resource `created`), first and last activity.
- [x] **P2 — Report.** `report.py` writes `site/`. Spec: `docs/specs/P2-report.md`. Static HTML in the repo: top-orgs heatmap (uploads per period; last 5 years, last year; top 50 = union of top by uploads and by datasets) and most active datasets (longest timespan, most uploads).
- [x] **P3a — Snapshots and diff, local part.** `snapshot.py`, `diff-snapshots.py`. Spec: `docs/specs/P3-snapshots.md`.
- [ ] **P3b — Weekly snapshots on GitHub Actions, release assets.** Spec: `docs/specs/P3b-snapshot-schedule.md`; brief ready. **Blocked:** `fetch-datasets.py` must be committed first (ingest work).
- [ ] P3c: retention of snapshot releases (about 900 MB a year expected). Scheduled, dated fetches; list new, changed and deleted datasets.
- [x] **P4 — Portal registry.** `portal-probe.py` → `docs/reference/portal-probe.csv`. Spec: `docs/specs/P4-portal-registry.md`.
- [x] **P5 — Choose portals to add.** Rule (user): Romania + EU national portals. List: `docs/reference/portals-selected.csv` (12 portals: 3 current, 1 RO, 8 EU national).
- [ ] **P6 — Fetch the new portals** (ingest work) and run P1 and P2 on them. ckan.govdata.de has 145k datasets: check time and disk first. Check the URLs in `docs/reference/ckan-instances.csv` (API works, dataset count, CKAN version); choose portals to add.
- [ ] katalog.data.go.id: the host does not resolve (DNS error, 2026-10-27). Check again before P1 runs.

## Bugs and defects

- [ ] Legacy `package-stats.csv` files have duplicate rows (data.gov.ro: 4766 rows, 3961 ids; data.humdata.org: 18350 rows, 17500 ids). See ANALYSIS.md section 2.
- [ ] Legacy data.humdata.org CSV: 3738 rows have empty `num_resources` and `org_name`. Cause not checked.

- [ ] `datasets.jsonl` is too large for GitHub: data.gov.ro 104 MB, data.humdata.org 965 MB (limit 100 MB per file). The ingest work must gitignore or compress it before anyone commits `data/`.
- [ ] data.humdata.org resource dates: 58156 of 191615 resources have `last_modified` before `created`. HDX probably resets `created` when a file is replaced. Study before HDX numbers are compared with other portals.
- [x] P1 spec ambiguity: "more than 1 day" for an update. The spec's measured counts (data.gov.ro 2033, africaopendata.org 1019) match a rule of 2 or more full days (`timedelta.days > 1`). The script uses strict "more than 24 hours" and gets 2045 and 1038. Resolved 2026-10-27: the script is right (strict, more than 24 hours); the spec table had a measurement error and is corrected.
- [x] `org-stats.py`: the `orgs` count in `summary.json` excludes `_none`; Confirmed 2026-10-27 and written into the spec.

- [ ] P3 later: compare resource `created` and `size` in the diff; stream the sort if a portal needs too much memory (HDX: 260 MB now).

- [ ] P2: check the pages in a real browser (360 px width, dark theme, tooltips, vertical month headers). Not done yet: the browser extension was not connected on 2026-10-27.
- [ ] P2: run the dataviz palette validator on the two heatmap ramps.
- [ ] P1/P2: add distinct datasets per org per year to P1 output, so the All-years tooltip is exact (now a sum of monthly counts).
- [ ] P2: accessibility — a table view or a texture for the heatmap.
- [ ] P2: test the portal base URL map (for example `data.gov.md` → `/ckan`).
- [ ] `.gitignore` has `/site` (from the Python template, for mkdocs). `site/` is committed with `git add -f`. Remove that line when the ingest session's `.gitignore` edits are committed.

- [ ] P4: deduplicate host aliases (data.qld.gov.au / www.data.qld.gov.au / geoscience; govdata.de / ckan.govdata.de; data.gov.uk / www.data.gov.uk) before portals are chosen.
- [ ] P4: probe again the 65 `timeout` and 54 `http_error` portals; some failures can be temporary.
- [ ] P4: examine the 1 `no_search` portal, and the `ok` portals with no `ckan_version`.

## Verified limits

- [-] data.gov.md CKAN API. Reason: `/ckan/api/3/action/status_show` and `/api/3/action/status_show` both return HTTP 404 (curl, 2026-10-27, also in the P4 probe). The portal does not expose the CKAN API now.

- [-] Add `private` and `state` to the slim snapshot record. Reason: `package_search` returns only public, active datasets, so these fields do not change between snapshots. A deletion shows as a missing dataset.

- [-] Backfill history from the legacy `package-stats.csv` files. Reason: duplicate rows, empty fields, no resource dates (ANALYSIS.md section 2). Decided 2026-10-27.
- [-] "One resource = one version" as the main metric. Reason: spike 2026-10-27; most multi-resource datasets got all files on the same day (ANALYSIS.md section 2).
