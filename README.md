# Pairwise70 Workbench

One offline program that **shows** every Pairwise70-family project in a single gallery
and lets you **run / reproduce** their analyses in one place — while leaving every
individual repo completely untouched.

> This is a *hub*. It does not re-implement any statistics. It embeds the proven HTML
> analysis engines verbatim and links the data/code repos. Update the source repos as
> usual; re-vendor here when you want the newer engine.

## Open it

Just open `index.html` in a browser (no build step, no server needed):

```
start index.html        # Windows
```

**Fully offline.** Plotly and the web fonts are vendored locally (`apps/vendor/`,
`assets/fonts/`), so the hub *and* the embedded engines — including their charts — work
with no internet connection.

## Tabs

| Tab | What it does |
|---|---|
| **Projects** | Gallery of every family project. Engines open live in *Analyze*; data/code repos link out (repo + live dashboard). |
| **Analyze** | Loads any embedded engine (PairwisePro v3.0, MAFI Calculator) in an iframe so you can run a real analysis. |
| **Benchmark** | The `pairwise70` cross-engine validation harness (vs the R metafor/meta oracle over the 7,545-MA Cochrane corpus). |
| **Reproduce** | Turns any analysis into a deterministic, exportable **run-record**: inputs + model + seed + app version → `run-record.json` + a runnable `reproduce.R` (metafor) snippet. |

## What's inside

```
index.html       # the hub (fully offline; my own code)
projects.json    # the project catalog — SINGLE SOURCE OF TRUTH (real metadata, no marketing)
catalog.js       # GENERATED from projects.json (file://-safe; do not edit by hand)
apps/            # vendored HTML engines (originals rewired to load assets locally)
  PairwisePro-v3.0-advanced.html
  MAFI-Calculator-Complete.html
  vendor/plotly-2.27.0.min.js   # vendored Plotly (offline charts)
assets/fonts/    # vendored web fonts (woff2 + localized CSS)
docs/spec.md     # scope, portfolio recon (reused vs net-new), non-goals
tests/           # validate.py + smoke.py + build_catalog.py
```

## Family projects shown

PairwisePro v3.0 · MAFI Calculator · Pairwise70 dataset (501 reviews / 7,545 MAs) ·
Reproduction-Floor Atlas · GRMA · GWAM · 786-MIII (Masroor). See `projects.json` for
links and analysis-type tags.

## Reproducibility

Every recorded run carries a seed (mulberry32 PRNG), the app version, and the exact
model settings, and exports both a JSON record and a `metafor` R script. Re-running the
same seed reproduces the same `determinismProbe` (asserted by `tests/smoke.py`). The R
snippet is meant to be checked against the `pairwise70` benchmark / R oracle to 1e-6.

## Adding a project

Edit **`projects.json` only** (the single source of truth), then regenerate the
`file://`-safe catalog:

```
python tests/build_catalog.py     # rewrites catalog.js from projects.json
```

`tests/validate.py` runs `build_catalog.py --check` and fails if `catalog.js` is stale,
so the two can never drift.

## Tests

```
python tests/validate.py     # 39 structural checks (incl. offline + catalog-sync)
python tests/smoke.py         # 11 headless-browser checks (needs Chrome + selenium)
```

## License & attribution

MIT. Embedded engines retain their original licenses from their source repos. Vendored
third-party assets: **Plotly.js** v2.27.0 (MIT, Plotly Inc.) under `apps/vendor/`;
**JetBrains Mono**, **Plus Jakarta Sans**, and **Inter** web fonts (SIL Open Font
License 1.1) under `assets/fonts/`. All are redistributable under this MIT repo.
