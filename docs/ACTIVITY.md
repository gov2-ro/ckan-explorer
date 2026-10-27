# Activity

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
