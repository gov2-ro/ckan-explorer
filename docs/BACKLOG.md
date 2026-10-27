# Backlog

Statuses: `[ ]` open, `[~]` in progress, `[x]` done, `[-]` dropped.

## Roadmap

- [x] Extract the 2023 notes into `docs/ANALYSIS.md` and `docs/reference/ckan-instances.csv`.
- [x] Set priorities from `docs/ANALYSIS.md` (sections 8 and 9).
- [x] **P1 — Org stats.** Spec: `docs/specs/P1-org-stats.md`. Brief for Sonnet: `docs/briefs/P1-org-stats.md`. Done 2026-10-27: `org-stats.py`, tests in `tests/`. For every working portal, read `datasets.jsonl` and write per-org and per-dataset tables: datasets, resources, uploads per month (resource `created`), first and last activity.
- [~] **P2 — Report.** Spec: `docs/specs/P2-report.md`; brief ready. Static HTML in the repo: top-orgs heatmap (uploads per period; last 5 years, last year; top 50 = union of top by uploads and by datasets) and most active datasets (longest timespan, most uploads).
- [~] **P3 — Snapshots and diff.** Spec (local part): `docs/specs/P3-snapshots.md`; brief ready. Storage, schedule and retention wait for the user. Scheduled, dated fetches; list new, changed and deleted datasets.
- [~] **P4 — Portal registry.** Spec: `docs/specs/P4-portal-registry.md`; brief ready. Check the URLs in `docs/reference/ckan-instances.csv` (API works, dataset count, CKAN version); choose portals to add.
- [ ] katalog.data.go.id: the host does not resolve (DNS error, 2026-10-27). Check again before P1 runs.

## Bugs and defects

- [ ] Legacy `package-stats.csv` files have duplicate rows (data.gov.ro: 4766 rows, 3961 ids; data.humdata.org: 18350 rows, 17500 ids). See ANALYSIS.md section 2.
- [ ] Legacy data.humdata.org CSV: 3738 rows have empty `num_resources` and `org_name`. Cause not checked.

- [ ] `datasets.jsonl` is too large for GitHub: data.gov.ro 104 MB, data.humdata.org 965 MB (limit 100 MB per file). The ingest work must gitignore or compress it before anyone commits `data/`.
- [ ] data.humdata.org resource dates: 58156 of 191615 resources have `last_modified` before `created`. HDX probably resets `created` when a file is replaced. Study before HDX numbers are compared with other portals.
- [x] P1 spec ambiguity: "more than 1 day" for an update. The spec's measured counts (data.gov.ro 2033, africaopendata.org 1019) match a rule of 2 or more full days (`timedelta.days > 1`). The script uses strict "more than 24 hours" and gets 2045 and 1038. Resolved 2026-10-27: the script is right (strict, more than 24 hours); the spec table had a measurement error and is corrected.
- [x] `org-stats.py`: the `orgs` count in `summary.json` excludes `_none`; Confirmed 2026-10-27 and written into the spec.

## Verified limits

- [-] Backfill history from the legacy `package-stats.csv` files. Reason: duplicate rows, empty fields, no resource dates (ANALYSIS.md section 2). Decided 2026-10-27.
- [-] "One resource = one version" as the main metric. Reason: spike 2026-10-27; most multi-resource datasets got all files on the same day (ANALYSIS.md section 2).
