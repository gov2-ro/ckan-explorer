# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python scripts that collect dataset metadata from public CKAN open-data portals (data.gov.ro, data.humdata.org, catalog.data.gov, data.gov.sg, africaopendata.org, katalog.data.go.id, ...) for analysis of publishing activity per organization. Background doc: [CKAN data analyzer](https://docs.google.com/document/d/1Emrco1IWSVUrHCGGPlFBf8qqCEucECJi/). There is no build, test suite, linter, or requirements file.

## Running (preferred)

Dependencies (install manually): `requests`, `tqdm`.

```sh
python fetch-datasets.py <ckan_instance_url> [--out DIR]   # default out: data/<hostname>/
```

`fetch-datasets.py` pages through `package_search` (rows=1000, `sort=id asc`, advancing `start` by the number of results actually returned, so portals that cap rows lower still work). It retries with backoff, fails fast on 4xx, and dedupes by id. Output in the out dir, overwritten each run: `package-stats.csv` (with header; columns `id, metadata_created, metadata_modified, num_resources, name, title, org, org_name, org_title`; `org` is JSON) and `datasets.jsonl` (raw packages, one per line). Prints reported count vs rows written and warns on mismatch. The list of known portal URLs is in its docstring. catalog.data.gov has 300k+ datasets; avoid it.

Known quirk: data.gov.md/ckan and data.gov.sg currently return 404 for the CKAN API; datastore.brussels is not CKAN-API compatible.

## Legacy two-step scripts

`list-packages.py` (package_list -> `{data_root}package-list.json`) and `get-stats.py` (one `package_show` per dataset -> `package-stats.csv`) still exist but are slow. Portal is chosen by editing the `ckan_instance`/`data_root` pair in **both** scripts; run from repo root. Existing `data/<host>/package-stats.csv` files were produced by them.

`data/package-list.json` and `data/package-stats.csv` at the top of `data/` are legacy outputs (data.gov.ro).

## Gotchas in legacy `get-stats.py`

- The CSV is opened in **append** mode: re-running duplicates rows unless the file is deleted first.
- No header row is ever written (condition never fires). Column order is as above; `org` is a Python repr, not JSON, so old and new CSVs differ in that column.
- Ends with macOS `say` (Romanian voice); `pandas` is imported but unused.

## Ignored paths

`_obsolete/` and `testbench/` (at any depth) are gitignored scratch areas; don't treat their contents as current code.

`data/` is gitignored: the repo tracks the tool only, and fetched results stay local. Don't commit outputs.



## Tone of voice

Follow Simplified Technical English (ASD-STE100) for docs, error messages and agent-facing
text:

- One instruction per sentence; at most ~20 words (procedures), ~25 (descriptive).
- Active voice; name the actor.
- Simple tenses.
- One word, one meaning; the same term every time.
- No noun clusters over three words; keep the articles.
- Keep every condition and qualifier.

## Process notes

Two files carry the project's memory between sessions. Create each one with the first work
that needs it, and read both before starting.

**`docs/BACKLOG.md`** — roadmap, tasks, bugs. Statuses: `[ ]` open, `[~]` in progress, `[x]`
done, `[-]` dropped.
- Flip an item to `[x]` in the same change that finishes it.
- Add a defect or deferred work when you find it.
- Mark a dead end `[-]` **with the reason**, under *Verified limits*, so that nobody
  investigates it again.

**`docs/ACTIVITY.md`** — dated entries, newest first, each with **Done / Hard / Decided**.
- Add an entry when a chunk of work lands.
- A decision carries its rationale and the cost of the alternative.
- Record wrong turns, and say what was measured and what was assumed. Keep the measured
  numbers: they are the baseline for regressions.

**Versions follow the work.** The project is spec-driven, so a spec, an ADR, a decision that
changes a spec, a set of named tests, and a measured spike are deliverables, as much as a
user capability is. After each committed chunk, check what changed since the last tag. For a
relevant deliverable, bump the minor version; for a correction only, bump the patch. 
Add a line to `docs/RELEASES.md`, commit, and tag the commit. Do this without asking, and say 
when you did. **Publishing a release is separate, and happens only when asked.**


## Opus designs, Sonnet builds

The work splits by model. **When you are Opus**, defer implementation and well-defined
future work to Sonnet by default:

- **Opus** writes specs, ADRs and briefs; makes and records decisions; and reviews Sonnet's
  results against the brief before they are accepted.
- **Sonnet** carries out a brief: code, spikes, measurements, fixture changes, and the
  activity and backlog entries for that work.
- **Opus does the work itself** when the task is a few lines, or when the design is still
  moving and the doing is part of the deciding.

**Sonnet stops and asks** when a step would change a spec, an ADR, an invariant or a
dependency outside the brief's folder. It reports what it measured and what it assumed.

To hand over, Opus tells the owner that the brief is ready. The owner runs it in a Sonnet
session, or asks Opus to start a Sonnet agent on it.