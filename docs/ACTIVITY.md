# Activity

## 2026-10-27 — Size and file-type stats; tile clean-up (user requests)

**Done**
- Added total file size and file-type shares: top tile and a type panel for the whole portal; a panel in the dataset section that follows the filters (so an organization filter gives the per-organization view); a "Size" column in the list and in the heatmap.
- Hid the "Datasets with no organization" tile when 0 (data.gov.ro, portal.opendata.dk). Hid the "Uploads" tile, list column and filter when uploads equal resources.
- Measured (all files, 1024-based units): data.gov.ro 98.7 GB over 17,299 of 39,804 files (43%), XML is 45.9% of files; africaopendata.org 4.1 GB, 899 of 19,573 files (5%); portal.opendata.dk 5.7 GB (decimal), 392 of 2,440 files. 46 tests pass.

**Decided**
- Answer to "resources vs uploads": an upload is a resource counted by the month of its `created` date (P1 spec). All three portals have 0 resources with no or bad `created`, so both numbers are equal everywhere (39,804; 19,573; 2,440). They would differ only for a resource with no valid date. Cost of hiding: if a portal later has such resources, the tile returns by itself.
- File-type bars show the share of file count, not of size, because size is missing for most files. Size per type is in the tooltip and label, where known. Bars use one hue and direct labels, no categorical colors (dataviz skill: identity is the label).

**Hard**
- Totals are lower bounds, because many resources have no size. The page says what share of files has one.

## 2026-10-27 — One dataset list, organization links, RSS (user requests)

**Done**
- Replaced the two dataset lists (P2 top-25 tables and the P7 browser) with one table: title, organization, resources, uploads, active months, first and last upload, timespan, modified. Columns sort; filters cover text, organization, format, modified in 7/30/365 days, minimum uploads, active months and years.
- Heatmap organization names and list organization cells link to the filtered list (`#org=<name>`). Links to the portal are small and say so ("portal ↗", "Open on <host> ↗").
- Added `site/<host>.rss.xml`: the 50 latest-modified datasets, links to the portal. Feed is valid XML for all three portals (data.gov.ro 24 KB).
- 44 tests pass. Stub-DOM run on portal.opendata.dk (631 datasets): 50 rows per page, row opens and closes, org click gives 14, modified in 30 days gives 6, uploads of 50 or more gives 2, reset gives 631.

**Hard**
- No real browser again (extension not connected). Layout of the wide table at 360 px is unchecked; the table scrolls in its own container.

**Decided**
- The P2 top tables stay as the fallback for a portal without `datasets.jsonl`. Cost: two code paths; the benefit is that stats-only portals keep a list.
- RSS items link to the portal, not to this site: the site has no public URL yet. Cost: the feed points off-site until a publish step exists.
- "Modified" is `metadata_modified` (any metadata change), not the date of the last upload; the last-upload column shows the latter.

## 2026-10-27 — Sample portal portal.opendata.dk; non-CKAN portals checked

**Done**
- Fetched portal.opendata.dk (631 datasets, 2,440 resources, 20 organizations) with `fetch-datasets.py`; ran `org-stats.py` and `report.py`. The page is 32 KB.
- Checked data.europa.eu, data.gov.sg and data.gov.my. All three return 404 on the CKAN API. Each has its own JSON API (see the backlog).

**Hard**
- `requests` and `tqdm` were not installed. I made a venv in the scratchpad and ran the fetch there. The system Python is unchanged.

**Decided**
- Only portal.opendata.dk as a sample (user). Cost: three portals only in the report until P6 runs.
- The non-CKAN portals stay out of this tool for now. Cost: no Singapore, Malaysia or EU-wide view.

## 2026-10-27 — Browser merged into the portal page; HDX data removed (user decisions)

**Done**
- Removed `data/data.humdata.org/` (970 MB: `datasets.jsonl` 965 MB, `package-stats.csv`, snapshot, stats) and `site/data.humdata.org.html`. `data/` is gitignored, so only a new `fetch-datasets.py` run brings it back.
- Merged the dataset browser into `site/<host>.html` as a "Datasets" section. `browse.py` is now a module that `report.py` calls; the separate `*-datasets.html` pages are gone. `report.py` writes `site/<host>-datasets.js` for each portal that has `datasets.jsonl`.
- Added `/site/*-datasets.js` to `.gitignore`. Amended specs P2 and P7.
- 39 tests pass. Page scripts pass `node --check`. Portal pages: data.gov.ro 75 KB, africaopendata.org 48 KB; index 3.8 KB.

**Decided**
- One page per portal, not two (user). Cost: the portal page needs `datasets.jsonl`, which P2 did not read before; a portal with only stats has no "Datasets" section.
- Keep data.gov.ro and africaopendata.org; add a few small sample portals (user, count not chosen).
- The HDX note stays in `report.py` (`PORTAL_NOTES`) for a later return.

## 2026-10-27 — P7 dataset browser and P8 spec (Sonnet)

**Done**
- Checked what `datasets.jsonl` already holds: the full package record, with all resources (format, size, created) and `datastore_active`. No resource has a schema or field list (data.gov.ro: 4,500 of 39,804 resources are `datastore_active`; africaopendata.org: 1,659 of 19,573).
- Searched for prior art for a portal-wide field fetch. Found none; `ckanapi dump` gives package metadata only. Decision: write `fetch-fields.py` (P8).
- Wrote specs `docs/specs/P7-dataset-browser.md` and `docs/specs/P8-fetch-fields.md`.
- Built `browse.py` (P7) and `tests/test_browse.py` (10 tests; all 38 tests pass). `report.py` now links to the dataset pages when they exist.
- Measured: datasets 28,832 on HDX (the spec draft guessed 17,000). Data files: data.gov.ro 6.6 MB, africaopendata.org 5.0 MB, HDX 37.7 MB. HTML files about 10 KB.

**Hard**
- The browser extension was not connected. I checked the page script with `node --check` and a stub-DOM run only (render, open a row, search, no match). Layout, dark theme and phone width are not checked.

**Decided**
- Data goes in a separate `.js` file, not inline. Rationale: `fetch()` fails on `file://`, and a `<script src>` works. Cost: a page is two files, not one (P2 rule relaxed for P7 only).
- Fields UI is in the page but appears only when `has_fields` is true. Cost: about 1 KB of unused code until P8 runs.
- Dataset text is cut to 300 characters and resource names to 120 to limit size. Cost: the full notes are on the portal only.

## 2026-10-27 — Skip large portals; .gitignore fixed

**Done**
- Added the column `active` to `docs/reference/portals-selected.csv`. Active: 7 portals under 10,000 datasets. Not active: ckan.govdata.de, data.humdata.org, data.gov.gr, data.gov.ie, data.overheid.nl.
- Removed `/site` (mkdocs template line) from `.gitignore`.
- Committed the ingest session's `.gitignore` edits (`/docs/reference/init/*`, `/data/`) and its staged removal of 10 legacy data files from the index. The files stay on disk.

**Decided**
- Large portals are skipped during development (user). Threshold: 10,000 datasets, by Opus. Rationale: the next portal under it has 9,326 datasets (podatki.gov.si); the ones above it start at 20,760. Cost: no large-portal comparison until they are activated.
- data.humdata.org keeps its existing stats and report page, but is not active for new fetches and weekly snapshots.

## 2026-10-27 — User decisions after P1–P4

**Done**
- Recorded the user's decisions in ANALYSIS.md section 9.
- Wrote `docs/reference/portals-selected.csv` from the P4 probe, and the P3b spec and brief.

**Decided**
- Snapshots (user): weekly, as GitHub release assets. Cost of the alternatives: commits in git grow the history forever (about 200 MB a year for monthly); local cron has no backup and no sharing.
- Portals (user): Romania + EU national portals. Opus chose the list from the probe: data.primariatm.ro, ckan.govdata.de, data.gov.gr, data.gov.ie, data.overheid.nl, podatki.gov.si, avoindata.fi, data.gov.lv, portal.opendata.dk. Left out: opendata.hu (72 datasets, CKAN 2.0, not the official portal), regional and city portals, and EU national portals that are not CKAN or did not answer (data.gov.cz, data.gov.sk, data.gov.hr, data.gv.at, danepubliczne.gov.pl, data.europa.eu, datasets.catalogue.data.gov.dk).
- katalog.data.go.id is not in the list: it gave a DNS error on 2026-10-27 and was not in the probe result as `ok`.
- HDX (user): keep it with the note.
- Publish (user): push the commits and tags; no GitHub Pages yet.
- P3b is blocked until `fetch-datasets.py` is committed. A weekly job that fails each week is worse than no job.

## 2026-10-27 — P4 portal probe built (Sonnet) and reviewed (Opus)

**Done**
- Sonnet built `portal-probe.py` with 7 tests (local `http.server`, no network). One full run on 526 URLs: 491 s with 8 workers.
- Result in `docs/reference/portal-probe.csv`: ok 170, no_search 1, not_ckan 106, http_error 54, timeout 65, dns_error 81, tls_error 33, conn_error 16. Size bands of `ok`: under 100: 49; 100–999: 60; 1000–9999: 33; 10000–99999: 21; 100000 or more: 7.
- Largest `ok`: b2find.eudat.eu 1,473,955 datasets; geoscience.data.qld.gov.au 192,766; data.qld.gov.au 188,891; govdata.de 145,214; data.gov.au 141,332.
- `ok` in Romania: data.gov.ro (5260, CKAN 2.8.3) and data.primariatm.ro (36, CKAN 2.10.11). 47 `ok` portals have an EU country-code host.
- Opus review: tests pass; the CSV has 526 rows, sorted. Checked data.gov.md by hand: HTTP 404 on both API paths. This is the portal, not the probe.

**Hard**
- 280 of 526 candidates do not answer as CKAN. The 2023 list is old.
- Several portals appear under more than one host name.

**Decided**
- Amend the P4 spec to match two builder choices: a network failure on `status_show` skips `package_search` (avoids double timeouts), and `site_url` is not recorded.
- Mark data.gov.md as a verified limit.

## 2026-10-27 — P2 report built (Sonnet) and reviewed (Opus)

**Done**
- Sonnet built `report.py` with 7 tests and the fixture `tests/fixtures/stats-mini/`. It writes `site/index.html` and one page per portal.
- Measured: 0.28 s for 3 portals. Page sizes: data.gov.ro 68,419 bytes, data.humdata.org 72,622, africaopendata.org 40,821, index 4,217. Two runs give the same bytes. `node --check` passes on the inline scripts. A DOM stub in node clicked every view, sort and table button without errors. 12-month view rows: 56 (ro), 63 (HDX), 8 (africa).
- Opus review: all tests pass; no `innerHTML` in `report.py`; no external script or stylesheet; light and dark ramps are monotonic; a rerun gives the same files.

**Hard**
- Not checked in a real browser (the extension was not connected). Layout at 360 px, dark theme and tooltips are not verified.
- `org-monthly.csv` has no distinct dataset count per year. The All-years tooltip shows a sum of monthly counts and says so.

**Decided**
- Commit `site/` (the spec says the pages are files in the repo), with `git add -f`, because the template `.gitignore` ignores `/site`.
- Accept the builder's choices: per-view log scale with 5 steps; the "datasets" column and the top-50-by-datasets rule use all-time counts; datasets with 0 uploads are not in the tables.

## 2026-10-27 — P3 local part built (Sonnet) and reviewed (Opus)

**Done**
- Sonnet built `snapshot.py` and `diff-snapshots.py`, with 6 tests.
- Measured snapshot size, time and peak memory: data.gov.ro 2,782,561 bytes, 0.9 s, 76 MB; africaopendata.org 1,729,274 bytes, 0.5 s, 42 MB; data.humdata.org 12,412,908 bytes, 6.4 s, 260 MB.
- Real-data diff test on a changed copy of data.gov.ro (3 lines deleted, 1 title and 1 resource format changed): `added=0 deleted=3 changed=2`.
- Opus review: tests pass; a self-diff of the real snapshot gives 0/0/0; a second run does not overwrite.

**Hard**
- The snapshot sorts records in memory. HDX needs 260 MB; a much larger portal can need more.

**Decided**
- In the slim record, `org_name` is null for a dataset with no organization (P1 uses `_none`). Accepted: snapshots keep the source value; the `_none` group is a stats rule.
- Snapshots stay out of git until the user decides storage. `/data/` is now gitignored (ingest work).

## 2026-10-27 — P2, P3, P4 specs and briefs

**Done**
- Wrote specs and briefs for P2 (static report), P3 (snapshots and diff, local part) and P4 (portal probe).

**Decided**
- Build P2, P3 and P4 in parallel with three Sonnet agents. The agents do not commit or edit the process files; Opus reviews and commits. Rationale: the three parts use different files, and one committer avoids git conflicts and tag races.
- P2 pages are self-contained (inline CSS/JS, embedded JSON). Rationale: they work from `file://` and on GitHub Pages without a build. Cost: data is duplicated in each page (under 1 MB each).
- P2 heatmap uses a log color scale. Rationale: uploads per org have a heavy tail (data.gov.ro: ANPM 16752, median org much lower).
- P3 snapshots are slim (selected fields, gzip). Rationale: the full HDX file is 965 MB. Cost: a diff cannot see changes in fields outside the slim record.
- P3 storage, schedule and retention are left to the user.

## 2026-10-27 — P1 review (Opus)

**Done**
- Reviewed the P1 build (`ba6c5ff`, v0.4.0) against the spec. Ran the 8 tests: OK. Checked `summary.json` for data.gov.ro: all 4 invariants true. Checked the window code (as-of month and the 11 or 59 months before it) and the update rule (strict, more than 24 hours).
- Accepted P1.

**Hard**
- The spec's update counts (2033, 92995, 1019) came from Opus's measurement script, which used `timedelta.days > 1` (2 or more full days). That does not match the spec text. Sonnet followed the text and found the difference.

**Decided**
- Keep the spec text (more than 24 hours). Corrected the spec table to 2045, 94355 and 1038. Cost of the alternative (2 full days): a rule that nobody chose on purpose.
- `orgs` in `summary.json` excludes `_none`; written into the spec.

## 2026-10-27 — P1 org stats built

**Done**
- Wrote `org-stats.py` (standard library only, line-by-line read) and `tests/test_org_stats.py` with `tests/fixtures/mini.jsonl`. Result of `python3 -m unittest discover tests`: `Ran 8 tests ... OK`.
- Ran `python3 org-stats.py --all`. All 4 invariants hold on all 3 portals. Output is in `data/<host>/stats/` (not committed).

**Measured** (one run per portal; time and peak memory from `/usr/bin/time -l`)

| Portal | Datasets | Resources | Uploads | Updates | Orgs | No-org datasets | As-of | Time | Peak memory |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| data.gov.ro | 5260 | 39804 | 39804 | 2045 | 131 | 0 | 2026-10-27 | 0.9 s | 57 MB |
| data.humdata.org | 28832 | 191615 | 191615 | 94355 | 376 | 0 | 2026-10-27 | 6.3 s | 153 MB |
| africaopendata.org | 6982 | 19573 | 19573 | 1038 | 182 | 1974 | 2026-10-26 | 0.4 s | 35 MB |

Top 10 organizations by `uploads` (all time):
- data.gov.ro: agentia-nationala-pentru-protectia-mediului 16752; mdrap 6822; mfp 2889; mj 1930; ms 1479; casa-nationala-de-asigurari-de-sanatate 1432; inspectoratul-general-pentru-situatii-de-urgenta 628; agentia-nationala-pentru-ocuparea-fortei-de-munca 489; onrc 480; ancpi 473.
- data.humdata.org: worldpop 72338; hot 22315; fewsnet 19540; world-health-organization 7534; dhs 6576; world-bank-group 4790; copernicus 4764; heidelberg-institute-for-geoinformation-technology 4131; unhcr 3943; meta 3228.
- africaopendata.org: vulekamali 5589; _none 3969; displacement-tracking-matrix 1018; grid-3-nigeria 1000; tanzania-national-bureau-of-statistics 780; the-charter-project 773; sensors-africa 647; digital-earth-africa 511; ilri 478; code-for-africa 475.

Top 10 organizations by `uploads_12m`:
- data.gov.ro: mdrap 926; mfp 478; casa-nationala-de-asigurari-de-sanatate 287; mj 120; onrc 99; ms 64; institutul-national-de-statistica 54; cancelaria-prim-ministrului 53; agentia-nationala-pentru-ocuparea-fortei-de-munca 52; inspectoratul-general-pentru-situatii-de-urgenta 39.
- data.humdata.org: hot 22112; fewsnet 13254; heidelberg-institute-for-geoinformation-technology 3657; climate-trace 1617; unep-wcmc 1504; copernicus 1181; healthsites 930; automated-disaster-analysis-mapping 768; fao 643; world-health-organization 588.
- africaopendata.org: sensors-africa 142; open-restitution-africa 31; code-for-africa 24; tanzania-national-bureau-of-statistics 18; displacement-tracking-matrix 7; ansd 2; maasaimarauniversity 2; ministere-de-la-sante-publique-republique-democratique-du-congo 2; _none 0.

**Hard**
- The update counts differ from the spec table (data.gov.ro 2045 vs 2033; africaopendata.org 1038 vs 1019). Resource counts, the "earlier" counts (58156 on HDX, 0 elsewhere) and no-org counts match. Both spec numbers match a rule of 2 or more full days (`timedelta.days > 1`); the spec text says "more than 1 day", and the script follows the text. Logged in BACKLOG.md. Not checked: the HDX "later" count under the 2-day rule.
- On data.humdata.org 58156 resources have `last_modified` before `created`; P2 must show the note.

**Assumed**
- `summary.json` `orgs` excludes `_none` (spec does not say). `summary.json` also has extra keys `uploads` and `updates`.
- Valid date = matches `YYYY-MM-DD[T ]HH:MM:SS` in the first 19 characters and parses; date-only values would count as invalid (none occur in the data).
- A resource with an empty or missing `created` counts as "no created"; any other bad value counts as "invalid".
- An update needs both dates valid. Updates in `org-monthly.csv` can fall in months with no uploads (`datasets` is then 0).
- The as-of date is the latest `metadata_modified` over all lines, including duplicates. A duplicate `id` line is skipped entirely (its resources are not counted).
- Windows are by calendar month: 12m = as-of month and the 11 months before it.
- `timespan_days` uses calendar-date difference between first and last upload.

## 2026-10-27 — P1 spec and brief

**Done**
- Wrote `docs/specs/P1-org-stats.md` (definitions, output files, invariants, interface) and `docs/briefs/P1-org-stats.md` for Sonnet.
- Measured resource dates on the full `datasets.jsonl` files from the ingest session. data.gov.ro: 39804 resources, 2033 with `last_modified` > `created` + 1 day, 0 the other way. data.humdata.org: 191615, 92995 later, 58156 earlier. africaopendata.org: 19573, 1019 later, 0 earlier; 1974 of 6982 datasets have no organization. No resource lacks `created`.

**Hard**
- HDX `created` dates are not reliable as first-upload dates. P1 does not fix this; P2 must show a note.
- `datasets.jsonl` sizes (104 MB, 965 MB) exceed the GitHub file limit.

**Decided**
- An update (`last_modified` more than 1 day after `created`) is a secondary metric. Rationale: on data.gov.ro, 5% of resources were replaced later, and `created` alone misses them. Cost of the alternative (uploads only): replacement activity is invisible.
- The as-of date comes from the data (latest `metadata_modified`), not from the clock. Rationale: reruns give the same output. Cost: a portal with no recent changes gets an older window.
- Datasets with no organization go to `_none`. Cost of dropping them: 28% of africaopendata.org would disappear.
- Output goes to `data/<host>/stats/` and is not committed until the data commit policy is set.

## 2026-10-27 — Priorities set

**Done**
- Spike: fetched the 1000 most recently modified datasets per portal with `package_search` and measured resource `created` dates. data.gov.ro: 454 multi-resource datasets, 167 with dates spread over 30 days. data.humdata.org: 283 and 19. africaopendata.org: 542 and 38. Median spread 0 days on all three. katalog.data.go.id: DNS error.
- Set priorities P1–P4 in `docs/BACKLOG.md`; recorded decisions in ANALYSIS.md section 9.

**Hard**
- The sample is biased to recently modified datasets. The numbers are a signal, not a census.
- The spike measured `created` only. If a replaced file keeps its old `created` date, uploads are undercounted (open question 7).

**Decided**
- Main metric: uploads per period, from resource `created` dates. Rationale: the spike shows that the resource count overstates activity. Cost of the alternative: org rankings driven by bulk uploads on one day.
- Order: P1 org stats, P2 report, P3 snapshots, P4 registry. Rationale: value from current data first. Cost: history before P3 starts is lost for deleted datasets.
- Output: static HTML in the repo. Cost of the alternative (hosted page or notebook): not versioned with the code, or not readable without tooling.
- No backfill from legacy CSVs. The 2023 xlsx and file downloads stay open, outside P1–P4.

## 2026-10-27 — Analysis of the 2023 notes

**Done**
- Read the 2023 notes in `docs/reference/init/` (doc, xlsx with a top-orgs pivot, `ckan-list` CSV).
- Wrote `docs/ANALYSIS.md`: purpose, data model and metrics, API notes, UI spec, history, portal coverage, prior art, old roadmap status, open questions.
- Extracted the big list of CKAN instances to `docs/reference/ckan-instances.csv`: 528 links in the doc, 523 unique; plus 3 new from `ckan-list`; total 526 URLs, 519 hosts.
- Measured the legacy CSVs (rows, unique ids, empty fields). The table is in ANALYSIS.md section 2.

**Hard**
- The notes folder is gitignored, so the analysis must hold all of its content.
- The 2023 xlsx uses other column names. The mapping comes from the column contents: `versions` is `num_resources`.

**Decided**
- Extract first; set priorities in a separate step. Cost of the alternative: goals set before the full content is visible can miss items.
- All portals have equal scope; data.gov.ro is not the first focus. Cost: per-portal checks (for example "one resource = one version") must be done for each portal.
- The instance list is data, not prose, so it goes to a CSV. Nobody checked the URLs.
- Assumed, not measured: publishers add each period's file as a new resource.
