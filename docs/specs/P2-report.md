# P2 — Static report (spec)

Status: accepted, 2026-10-27. Owner of changes: Opus. Background: `docs/ANALYSIS.md` section 4; input from P1 (`docs/specs/P1-org-stats.md`).

## Goal

For each portal, make one static HTML page that shows which organizations publish, and when. Make one index page that compares the portals. The pages are files in the repo; GitHub Pages can serve them later.

## Input

For each `data/<host>/stats/` directory that has `summary.json`: `orgs.csv`, `org-monthly.csv`, `datasets.csv`, `summary.json` (P1 output). The script only reads these files. It does not read `datasets.jsonl`.

## Output

The script writes to `site/` and overwrites the files each run:

- `site/index.html` — the portal index.
- `site/<host>.html` — one page per portal.

Rules for every page:

- One self-contained file: inline CSS and inline JavaScript. No external scripts, fonts, or stylesheets. The page works from `file://`.
- The data that the page needs is embedded as JSON in a `<script type="application/json">` element. The script escapes `<` as `<` in that JSON.
- Titles and names come from the portals and are untrusted. Escape them in HTML. In JavaScript, set text with `textContent`, never with `innerHTML` for data values.
- Deterministic: the same input gives the same bytes. Do not write the clock time; show the as-of date from `summary.json`.
- Light and dark themes through `prefers-color-scheme`. Colors are CSS custom properties on `:root`.
- Readable at phone width (360 px). Wide tables scroll inside their own container, not the page.
- Page size: under 1 MB each.

## Portal page

### Header

Portal host (link to the portal), as-of date, and the counts: datasets, resources, uploads, updates, organizations, datasets with no organization. If `datasets.jsonl` came from data.humdata.org, show this note: "On this portal, `created` dates are probably reset when a file is replaced. Upload counts can be too low for old data and too high for recent data." Keep a host → note map in the script, so other portals can get notes later.

### Top organizations heatmap

- One row per organization, one column per period. The cell color shows uploads in that period. The cell has a tooltip (`title`) with org title, period, uploads, updates, datasets.
- Three views, chosen with buttons:
  - **All years:** one column per calendar year, from the first upload year to the as-of year.
  - **Last 5 years:** one column per month, the 60 months that end with the as-of month.
  - **Last 12 months:** one column per month, the 12 months that end with the as-of month.
- Rows in a view: the union of the top 50 organizations by uploads in that view's window and the top 50 by `datasets`, without duplicates. Organizations with 0 uploads in the window are left out of that view.
- Sort, chosen with buttons: uploads in the window (default), last upload, datasets.
- Extra columns on the left: org title (link to `{portal}/organization/{org_name}`, no link for `_none`), uploads in the window, datasets.
- Color scale: sequential, one hue, log scale (counts have a heavy tail). 0 is the background color. Show a legend with 4–5 steps and their values.

### Most active datasets

Three tables, 25 rows each, chosen with buttons:

- **Longest timespan:** by `timespan_days`, then `uploads`.
- **Most active months:** by `active_months`, then `uploads`.
- **Most uploads:** by `uploads`, then `active_months`.

Columns: title (link to `{portal}/dataset/{name}`), organization title, uploads, active months, first upload, last upload, timespan (years, 1 decimal).

## Index page

One row per portal: host (link to its page), as-of date, datasets, uploads, organizations, uploads in the last 12 months, organizations with an upload in the last 12 months, share of uploads of the top 10 organizations (all time). Sort by datasets, descending.

## Portal base URL

The links need the portal base URL. Keep a host → base URL map in the script (for example `data.gov.md` → `https://data.gov.md/ckan`). The default is `https://<host>`.

## Interface

```sh
python report.py            # every data/*/stats/ with summary.json
python report.py --out site
```

Python standard library only.

## Out of scope

- Charts other than the heatmap and the tables.
- Publishing to GitHub Pages.
- Comparing HDX dates (see the backlog item).
