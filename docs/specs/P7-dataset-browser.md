# P7 — Dataset browser (spec)

Status: draft, 2026-10-27. Amended 2026-10-27 (user): the browser is a section of the P2 portal page, not a separate page; it replaces the P2 "Most active datasets" tables; organizations link to it; an RSS feed of recent updates. Input: `datasets.jsonl` (raw packages) and, when present, `fields.jsonl` (P8, `docs/specs/P8-fetch-fields.md`). Style: same rules as P2 (`docs/specs/P2-report.md`).

## Goal

For each portal, add to the P2 portal page a section where a person can search and filter all datasets, and open one dataset to see its metadata and resources. When field data exists, the page also shows the fields (columns) of each resource.

## Output

`report.py` calls `browse.py` (a module; it has no command line). Output in `site/`, overwritten each run:

- `site/<host>.html` — the P2 portal page, with a new section "Datasets" before the footer. The page has the section only when `data/<host>/datasets.jsonl` exists.
- `site/<host>.rss.xml` — RSS 2.0 feed of the 50 datasets with the latest `metadata_modified` (newest first). Items link to the dataset on the portal. `lastBuildDate` is the newest item date (no clock). The feed is tracked in git; it is small.
- `site/<host>-datasets.js` — the data, as `window.BROWSE = {...};`. A `<script src>` with a relative path works from `file://`; `fetch()` does not. The repo ignores these files (`.gitignore`): they are large, and a build step makes them.

## Rules

- Standard library only. No external scripts, fonts, or stylesheets.
- Titles, notes, tags and names come from the portals and are untrusted. In JavaScript, set text with `textContent`, never `innerHTML`. In the JS file, escape `<` as `<`.
- Deterministic: the same input gives the same bytes. No clock time; show the as-of date (the latest `metadata_modified` in the input).
- Light and dark themes, phone width 360 px. The section uses the CSS custom properties of the portal page.
- The script reads `datasets.jsonl` one line at a time. It does not load the whole file in memory.

## Data (`window.BROWSE`)

```
{ host, base, as_of,
  orgs:    { "<org name>": "<org title>", ... },   // datasets with no organization have org ""
  formats: [ "CSV", ... ],                          // sorted; upper case, leading "." removed, "" -> "?"
  has_fields: true | false,  has_stats: true | false,
  org_size: { "<org name or _none>": bytes },  totals: { files, sized, bytes },
  datasets: [ { name, title, org, created, modified, license, tags[], notes, res[], up?, am?, fu?, lu?, ts? } ] }
```

- `created`, `modified`: date only, `YYYY-MM-DD`.
- `up`, `am`, `fu`, `lu`, `ts`: uploads, active months, first upload, last upload, timespan in days (P1 columns `uploads`, `active_months`, `first_upload`, `last_upload`, `timespan_days`). Present when P1 stats have the dataset.
- `notes`: the first 300 characters. `tags`: tag `name` values.
- `res` items: `{ name, fmt, size, created, ds, fields?, total? }`. `fmt` is a value from `formats`. `created` is a date only. `size` is an integer or `null`. `ds` is true when `datastore_active` is true.
- `fields` (list of `[name, type]`) and `total` (row count) exist only when `fields.jsonl` has an `ok` record for the resource. `has_fields` is true when at least one resource has `fields`.
- Datasets are in portal `id` order (the id is not in the data). Resource names are cut at 120 characters.

## Page

- **One list.** The section replaces the P2 "Most active datasets" tables. A portal page without `datasets.jsonl` keeps those tables.
- **Columns:** title, organization, resources, uploads, active months, first upload, last upload, timespan (years), modified. The five publishing columns (from P1 `datasets.csv`, joined by dataset id) exist only when `has_stats` is true.
- **Sort:** a click on a column title sorts by it; a second click reverses. Default: modified, newest first. Ties: modified, then name.
- **Filters:** text search (title, name, tags, organization; all words must match); organization; format; modified in the last 7 days, 30 days, or year (counted back from the as-of date); minimum uploads; minimum active months; minimum timespan in years (the last three only when `has_stats`); a Reset button. Zero results show a message.
- **Rows:** a click on the title opens a detail row: notes, license, dates, tags, resource table, and the link "Open on <host> ↗" (the only link to the portal in the list; it is secondary and names the portal).
- **Organization links:** the organization cell in the list, and the organization name in the P2 heatmap, link to `#org=<name>` (`_none` for datasets with no organization). A click sets the organization filter and scrolls to the section. A page opened with that hash starts filtered. The heatmap also keeps a small "portal ↗" link to the organization page on the portal.
- **RSS:** a link in the section text and a `<link rel="alternate">` in the page head.
- **Size and file types (amended 2026-10-27, user).** A "Size" column (sum of the known resource sizes of the dataset). A panel above the list covers the datasets that match the current filters: datasets, files, total size, how many files have a known size, and the share of each file type by number of files (top 8 and "Other"), each with its file count and size. With the organization filter set, the panel is the per-organization view; with no filter it is the global view. The page top shows the same panel for the whole portal, and a tile with the total size. The heatmap has a "Size" column per organization. Sizes are summed over files that have a size; the text says what share of files that is (data.gov.ro 43%, africaopendata.org 5%). Units are 1024-based.
- **Uploads equal resources.** An upload is a resource counted in the month of its creation date (P1). When every resource has a creation date, the two numbers are equal. Then the page hides the "Uploads" tile, the "Uploads" column and the "Min uploads" filter, and the "Resources" column is labelled "Resources (= uploads)". The "Datasets with no organization" tile is hidden when it is 0.
- **Fields (hidden until data exists):** the code is always in the page. When `has_fields` is true, a "Fields" filter appears, and each resource with fields gets a "Fields" toggle that lists `name — type` and the row count. When `has_fields` is false, no field control is in the DOM.

## Interface

```sh
python report.py --data data --out site
```

## Size

HDX is large (about 17,000 datasets). The data file for HDX can be several MB. This is accepted; the HTML file grows by under 10 KB.

## Out of scope

Resource download links, the dataset full text search index, charts, and any fetching (P8 fetches).
