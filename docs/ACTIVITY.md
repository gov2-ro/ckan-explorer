# Activity

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
