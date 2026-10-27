# P7 — Dataset browser (spec)

Status: draft, 2026-10-27. Amended 2026-10-27 (user): the browser is a section of the P2 portal page, not a separate page. Input: `datasets.jsonl` (raw packages) and, when present, `fields.jsonl` (P8, `docs/specs/P8-fetch-fields.md`). Style: same rules as P2 (`docs/specs/P2-report.md`).

## Goal

For each portal, add to the P2 portal page a section where a person can search and filter all datasets, and open one dataset to see its metadata and resources. When field data exists, the page also shows the fields (columns) of each resource.

## Output

`report.py` calls `browse.py` (a module; it has no command line). Output in `site/`, overwritten each run:

- `site/<host>.html` — the P2 portal page, with a new section "Datasets" before the footer. The page has the section only when `data/<host>/datasets.jsonl` exists.
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
  has_fields: true | false,
  datasets: [ { name, title, org, created, modified, license, tags[], notes, res[] } ] }
```

- `created`, `modified`: date only, `YYYY-MM-DD`.
- `notes`: the first 300 characters. `tags`: tag `name` values.
- `res` items: `{ name, fmt, size, created, ds, fields?, total? }`. `fmt` is a value from `formats`. `created` is a date only. `size` is an integer or `null`. `ds` is true when `datastore_active` is true.
- `fields` (list of `[name, type]`) and `total` (row count) exist only when `fields.jsonl` has an `ok` record for the resource. `has_fields` is true when at least one resource has `fields`.
- Datasets are in portal `id` order (the id is not in the data). Resource names are cut at 120 characters.

## Page

- **Header:** the section title and the count of datasets shown and total.
- **Controls:** a text search (title, name, tags, organization title; case-insensitive, all words must match); a select for organization; a select for format; a sort select (last modified, created, most resources, title); a page size of 50 with Previous and Next buttons.
- **Rows:** title (link to `{base}/dataset/{name}`), organization, number of resources, formats, last modified. Opening a row shows notes, tags, license, and a table of resources (name, format, size, created).
- **Fields (hidden until data exists):** the code for fields is always in the page. The page shows it only when `has_fields` is true. Then each resource with fields gets a "Fields" toggle that lists `name — type` and the row count. A select filter "has fields" appears. When `has_fields` is false, no field control is in the DOM.
- Zero results show a message, not an empty table.

## Interface

```sh
python report.py --data data --out site
```

## Size

HDX is large (about 17,000 datasets). The data file for HDX can be several MB. This is accepted; the HTML file grows by under 10 KB.

## Out of scope

Resource download links, the dataset full text search index, charts, and any fetching (P8 fetches).
