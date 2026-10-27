# CKAN explorer — analysis

This document collects the 2023 project notes and restructures them. The sources are in `docs/reference/init/` (gitignored, local only):

- `CKAN explorer.docx` (also exported as `.md` and `.pdf`; same text, no images). Online: [CKAN data analyzer](https://docs.google.com/document/d/1Emrco1IWSVUrHCGGPlFBf8qqCEucECJi/).
- `package-stats.xlsx` — data.gov.ro stats from 2023-09-03, with a pivot of top organizations. Online: [package-stats.xlsx](https://docs.google.com/spreadsheets/d/1EpcRd87dyQDIulUvQ0uLLds57Hplcqzb).
- `ckan-list.xlsx - Sheet1.csv` — 10 portals that the project tried. Online: [ckan-list.xlsx](https://docs.google.com/spreadsheets/d/1EpvOBXUHGoKVG8lsSnQo73rZJRsnZ7lJ/).

This document does not set priorities. A later step sets them (see `docs/BACKLOG.md`). The scope is all portals equally.

## 1. Purpose and questions

The project measures the publishing activity of each organization on public CKAN portals. It also compares portals.

The notes imply these questions:

1. Which organizations publish the most datasets and the most versions?
2. Which organizations are still active (last year, last 5 years)?
3. Which datasets get updates over a long time, and how often?
4. How does activity change over time, per portal and per organization?
5. How do portals compare in size, activity and concentration of publishers?

## 2. Data model and metrics

### 2023 column mapping

The 2023 sheet `package-stats` uses other column names. They map to the current CSV columns as follows:

| 2023 column | Current column | Meaning |
|---|---|---|
| `id` | `id` | Dataset UUID |
| `date1` | `metadata_created` | Dataset creation time |
| `date2` | `metadata_modified` | Last metadata change |
| `versions` | `num_resources` | Number of resources (files/links) |
| `slug` | `name` | Dataset URL name |
| `nume` | `title` | Dataset title |
| `Org-name` | `org_title` | Organization display name |
| `org` | `org_name` | Organization slug |

### "Version" = one resource

The notes count one resource as one "version". The reason: publishers often add each period's file (a month, a year) as a new resource of the same dataset. Thus the resource count measures update activity better than `metadata_modified`, which keeps only the last change.

This publishing practice was **assumed** from data.gov.ro. A spike on 2026-10-27 measured it. The sample is the 1000 most recently modified datasets per portal, so it is biased to active datasets:

| Portal | Datasets with more than 1 resource | Of these, resource `created` dates spread over more than 30 days |
|---|---:|---:|
| data.gov.ro | 454 (45%) | 167 |
| data.humdata.org | 283 (28%) | 19 |
| africaopendata.org | 542 (54%) | 38 |

Result: the practice is partly true on data.gov.ro and rare on the other portals. The median spread is 0 days on all three: most multi-resource datasets got all their files on the same day. Thus the resource count overstates activity.

**Decision (2026-10-27):** the main metric is **uploads per period** — resources counted by the month (or year) of their `created` date. Resources and datasets stay as secondary metrics.

### Metrics from the notes

- **SUM of versions** per organization — total resources.
- **COUNT of datasets** per organization (the pivot calls it "COUNT of versions").
- **Last update** per organization or dataset.
- **Versions last year** per organization.
- **Timespan** per dataset — from first to last activity.

### Timeline from resource dates

Each resource in a `package_search` or `package_show` result has `created` and `last_modified` fields. `fetch-datasets.py` writes the raw packages to `datasets.jsonl`, so these fields are available after one fetch. They give a per-upload timeline with no extra API calls. Note: the legacy `package-stats.csv` files do not have these fields.

### Legacy data quality (measured 2026-10-27)

The legacy CSVs have no header row, and `get-stats.py` appends, so a second run duplicates rows.

| Portal | Rows | Unique ids | Rows with empty `num_resources` | Rows with empty `org_name` |
|---|---:|---:|---:|---:|
| africaopendata.org | 5800 | 5800 | 20 | 1491 |
| data.gov.md | 1176 | 1176 | 0 | 11 |
| data.gov.ro | 4766 | 3961 | 15 | 15 |
| data.gov.sg | 1945 | 1945 | 0 | 0 |
| data.humdata.org | 18350 | 17500 | 3738 | 3738 |
| katalog.data.go.id | 2800 | 2800 | 0 | 0 |

Datasets without an organization need a rule (for example, an "(no organization)" group).

## 3. CKAN API notes

| Call | Use |
|---|---|
| `{ckan}/api/3/action/package_list` | All dataset names. Legacy step 1 (`list-packages.py`). |
| `{ckan}/api/3/action/package_show?id=<name>` | One dataset. Legacy step 2 (`get-stats.py`), one call per dataset; slow. |
| `{ckan}/api/3/action/package_search?q=*:*&sort=metadata_modified+desc&rows=20` | The 20 most recently changed datasets. Basis for a daily fetch of changes. |
| `package_search` with paging | All datasets in pages. Used by `fetch-datasets.py` (current). |

Example: [data.gov.ro, 20 freshest datasets](https://data.gov.ro/api/3/action/package_search?q=*:*&sort=metadata_modified+desc&rows=20). In 2023 these included `transparenta-covid`, `lista-entitatilor-publice-actualizata-la-data-de-01-08-2023` and `mecanismul-de-feed-back-al-pacientului-2023`.

The notes also name three levels for the data: organization, dataset, file (resource).

## 4. Outputs (UI spec from the notes)

The notes define two views. Both must work for every portal.

### Top organizations

- A heatmap table: one row per organization, one column per time period. The cell shows activity (versions) in that period.
- Time ranges: the last 5 years, and the last year.
- Sort orders: by total versions, by last update, by versions in the last year.
- Selection of the top 50:
  - A: the top 50 by SUM of versions.
  - B: the top 50 by COUNT of datasets.
  - Show A + B, without duplicates.

### Most active datasets

- By the longest timespan.
- By the most versions.

## 5. History and timeline

The 2023 roadmap asks for history:

- An activity timeline with all updates.
- Historical data, and a check for data updates (a scraper).
- Historical stats from [data.gov.ro/stats](https://data.gov.ro/stats).
- A daily fetch of updated packages.
- Yearly consolidated data.

Notes for later design:

- `package_search` does not return deleted datasets. To see deletions and growth, the project must keep dated snapshots.
- Resource dates (section 2) give the past timeline of datasets that still exist. They do not show deleted datasets.
- Existing baselines: the 2023 xlsx (data.gov.ro, 2023-09-03), the legacy CSVs in `data/<host>/`, and `data/_obsolete/` copies (for example `package-stats (Copy 230904).csv`).

## 6. Portal coverage

### Current portals

| Portal | Status |
|---|---|
| data.gov.ro | Works. |
| data.humdata.org | Works. |
| africaopendata.org | Works. |
| katalog.data.go.id | Works. |
| catalog.data.gov | Works, but has 300k+ datasets. Avoid it for now. |
| data.gov.md/ckan | CKAN API returns 404 (now). Legacy data exists. |
| data.gov.sg | CKAN API returns 404 (now). Legacy data exists. |
| datastore.brussels | Not compatible with the CKAN API. |

### New portals from `ckan-list`

| Portal | Note |
|---|---|
| data.primariatm.ro | Timișoara city hall. Not tried in code. |
| www.data.gov.uk | Not tried in code. |
| iasi.oras.digital | Marked "not ckan" (API at `/api/resources/`). |

### Candidate portals

[ckan-instances.csv](reference/ckan-instances.csv) has 526 portal URLs (519 hosts). The source is the big list from the [CKAN Instance Analysis](https://civicdataecosystem.org/2023/06/19/analysis.html) ([pose-ckan-analysis](https://github.com/rossreillypitt/pose-ckan-analysis)), merged with `ckan-list`. Some entries are not CKAN roots (for example search pages or IP addresses). Nobody checked these URLs.

Other sources to find portals:

- [Datashades.info](https://datashades.info/) — CKAN portals across the globe.
- [Data Portals](https://dataportals.org/), and the [okfn_dataportals.xlsx](https://docs.google.com/spreadsheets/d/1F5DzZes36JBensocmAOzcs2Ne3CPd0GU) sheet.
- [ckan.org/showcase](https://ckan.org/showcase).

### Showcase portals (from ckan.org)

- [open.toronto.ca](https://open.toronto.ca/), [open.canada.ca](https://open.canada.ca/en/open-data), [data.ontario.ca](https://data.ontario.ca/).
- [Australian Government](https://data.gov.au/) — public data from over 800 organisations.
- [Government of Canada](https://www.canada.ca/en.html) — tens of thousands of datasets.
- [Singapore Government](https://data.gov.sg/) — economic, education, environment, finance and health data.
- [Open Africa](https://africaopendata.org/) — aims to be the largest repository of data on Africa. Part of the Ujuzi Initiative (AMI, World Bank Institute, Google).
- [Open Data Denmark](https://www.opendata.dk/) — Danish municipalities and regions, common portal since 2016.
- [Helsinki Region Infoshare](https://hri.fi/en_gb/) — over 900 datasets, in Finnish and English.
- [United States Government](https://www.data.gov/) — moved to CKAN in 2013.
- [Energi Data Service](https://www.energidataservice.dk/) — data about the Danish energy system.
- [Humanitarian Data Exchange (HDX)](https://data.humdata.org/) — lets organisations with sensitive data show their work without sharing the data.
- [National Grid ESO](https://www.nationalgrideso.com/) — energy data for Great Britain.
- (LEGO — an internal data hub; struck out in the notes, not public.)

## 7. Prior art and inspiration

- [deathy/data-gov-ro-data-download](https://github.com/deathy/data-gov-ro-data-download) — downloads the actual files of data.gov.ro.
- [CKAN Instance Analysis](https://civicdataecosystem.org/2023/06/19/analysis.html) and [rossreillypitt/pose-ckan-analysis](https://github.com/rossreillypitt/pose-ckan-analysis) — a cross-portal analysis of CKAN instances. It is the source of the big portal list.
- [ckan/datapusher](https://github.com/ckan/datapusher) — a web service that pushes resource files into the CKAN DataStore.
- [data.gov.ro showcase](https://data.gov.ro/showcase) — apps that use data.gov.ro.
- [BaniiTai.info](https://baniitai.info/) — an app on public spending data.
- "gov2ro Github Scraping" — [a related project doc](https://docs.google.com/document/u/0/d/1DpAwGfp4lKbOuSsWmaJWmQOfZ1DC3aNr/edit).
- Project repo: [gov2-ro/ckan-explorer](https://github.com/gov2-ro/ckan-explorer).

## 8. Old roadmap, status today

Items from the 2023 doc and from `readme.md`. Status on 2026-10-27.

| Item | Source | Status |
|---|---|---|
| Fetch the dataset index | doc, readme | Done (`list-packages.py`; replaced by `fetch-datasets.py`). |
| Get stats per dataset | doc, readme | Done (`get-stats.py`; replaced by `fetch-datasets.py`). |
| Add header columns to the stats | readme | Done in `fetch-datasets.py`. Legacy CSVs still have no header. |
| Compile organization stats (`org-stats` script) | doc, readme | Open. Only the 2023 manual pivot exists. |
| Activity timeline, all updates | doc | Open. Data is available in `datasets.jsonl` (resource dates). |
| Historical data and update checks (scraper) | doc | Open. |
| Historical stats from data.gov.ro/stats | doc | Open. |
| Daily fetch of updated packages | doc | Open. |
| Prepare for GitHub Actions | readme | Open. |
| Consolidate yearly data | doc, readme | Open. |
| UI: top organizations heatmap, most active datasets | doc, readme | Open. |

## 9. Questions

### Decided (2026-10-27)

1. Main metric: **uploads per period** (section 2). Resources and datasets are secondary.
2. "One resource = one version" is partly true on data.gov.ro only (spike, section 2). The uploads metric does not depend on it.
3. Output: **static HTML in the repo**. GitHub Pages can serve it later.
4. Legacy CSVs: **no backfill**. They do not give history.
5. Priorities: P1 org stats, P2 report, P3 snapshots and diff, P4 portal registry. See `docs/BACKLOG.md`.
6. Datasets with no organization go to the group `_none` / "(no organization)". africaopendata.org has 1974 of 6982 such datasets.
7. Snapshots: **weekly**, stored as **GitHub release assets** (spec `docs/specs/P3b-snapshot-schedule.md`).
8. Portals to add: **Romania + EU national portals** (`docs/reference/portals-selected.csv`).
9. HDX: **keep it, with the note**; leave it out of cross-portal comparisons until its dates are studied.

### Still open

1. Do we use the 2023 xlsx (data.gov.ro, 2023-09-03) as one early history point? Not chosen now.
2. Do we download the actual files (as deathy/data-gov-ro-data-download does)? Not chosen now; not in P1–P4.
3. Does the CKAN activity stream (`package_activity_list`) give better history than resource dates? Since CKAN 2.10 it is an optional plugin, so some portals can disable it (not checked).
4. Does a resource keep its `created` date when the publisher replaces the file? Measured 2026-10-27: on data.gov.ro, 2045 of 39804 resources have `last_modified` more than 1 day after `created`; P1 counts these as updates. On data.humdata.org, 58156 of 191615 have `last_modified` before `created`, so HDX `created` is probably not the first upload. See `docs/specs/P1-org-stats.md`.
