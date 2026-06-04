# Pairwise70 Workbench

**Live:** https://mahmood726-cyber.github.io/pairwise70-workbench/

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
| **Story** | A data-story dashboard (the landing tab): the family's central reproduction-floor finding told with charts drawn from **real recorded data** (gauge, bars, stat tiles) via the offline chart-kit. |
| **Projects** | Gallery of every family project. Engines open live in *Analyze*; data/code repos link out (repo + live dashboard). |
| **Analyze** | Loads any embedded engine (PairwisePro v3.0, MAFI Calculator) in an iframe so you can run a real analysis. |
| **Benchmark** | Real engine-vs-`metafor` agreement: 100 reviews plotted on the identity line (max \|Δθ\| ≈ 6e-06), from `Pairwise70/ma4_metafor_validation.csv`, plus the harness list. |
| **E156 Papers** | The family's E156 micro-papers (real bodies from each repo), with **live contract validation** — sentence count and word count checked against the seven-sentence / ≤156-word E156 rule in the browser. |
| **Reproduce** | Turns any analysis into an exportable **manifest**: inputs + model + seed + app version + input digest → `run-record.json` + a runnable `reproduce.R` (metafor) snippet. |

### The Story dashboard

The landing tab is a scrollytelling dashboard built with classical narrative devices used
purely as craft (no religious content): **ring composition** (opens and closes on the same
number, 0.005), a **recurring refrain**, a **parable**, **gradual disclosure** of the figures,
a **shift of address** from "they" to "you", and **contrast pairs** (counts vs. means). Every
chart uses real data — the 14.3% reproduction floor (overall) and the 12.9% / 25.0% / 27.0%
by-outcome breakdown come straight from `repro-floor-atlas`'s `baseline.json`; family
composition is derived from the catalog. A "Narrative method" note on the page states the
techniques explicitly and that they are rhetorical only.

## What's inside

```
index.html       # the hub (fully offline; my own code)
projects.json    # the project catalog — SINGLE SOURCE OF TRUTH (real metadata, no marketing)
catalog.js       # GENERATED from projects.json (file://-safe; do not edit by hand)
papers.js        # E156 micro-paper bodies (real text from each repo's e156-submission)
apps/            # vendored HTML engines (originals rewired to load assets locally)
  PairwisePro-v3.0-advanced.html
  MAFI-Calculator-Complete.html
  vendor/plotly-2.27.0.min.js   # vendored Plotly (offline charts)
  vendor/chartkit.js            # vendored e156 chart-kit (27 offline SVG primitives)
assets/fonts/    # vendored web fonts (woff2 + localized CSS) + OFL license texts
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
python tests/validate.py     # 99 structural checks (offline, catalog-sync, R-correctness, a11y, licenses, story/papers/charts)
python tests/smoke.py         # 36 headless-browser checks (needs Chrome + selenium)
python tools/build_ma4_data.py   # regenerate data/ma4.js from the real Pairwise70 CSVs + .rda
```

Chart types now in use (all real data, offline via the chart-kit):
- **gauge** — reproduction floor (14.3%)
- **bars** — by-outcome, family-by-kind, analysis-type frequency
- **stat tiles** — corpus scale + benchmark agreement summary
- **forest plot** — six pooled risk ratios of a real Cochrane review (`CD000028_pub4`), metafor-validated
- **funnel plot** — the 13 trials inside its all-cause-mortality outcome (per-study logRR vs SE)
- **prediction-interval zone** — pooled RR with 95% CI and the wider 95% PI (`t_{k-1}·√(τ²+SE²)`)
- **leave-one-out** — random-effects re-pool dropping each of the 13 trials
- **cumulative** — random-effects re-pool entering the 13 trials by year
- **GOSH** — pooled RR vs I² across 2,500 of the 8,178 ≥2-trial subsets
- **heterogeneity density** — τ across 1,168 risk-ratio meta-analyses (Gaussian KDE)
- **capability matrix** (traffic-light) — which analysis each project supports, derived from the catalog
- **agreement scatter** — engine vs `metafor` across 100 reviews

The forest/funnel/benchmark numbers come from `Pairwise70`'s `ma4_*.csv` and `*_data.rda`
(read via `pyreadr`, no R needed) by `tools/build_ma4_data.py`, which fails closed if the
source files are missing. The shipped `data/ma4.js` holds numbers only.

## License & attribution

MIT. Embedded engines retain their original licenses from their source repos. Vendored
third-party assets: **Plotly.js** v2.27.0 (MIT, Plotly Inc.) under `apps/vendor/`;
**JetBrains Mono**, **Plus Jakarta Sans**, and **Inter** web fonts (SIL Open Font
License 1.1) under `assets/fonts/`, with their OFL texts bundled alongside. See
[`THIRD-PARTY-LICENSES.md`](THIRD-PARTY-LICENSES.md).

## Notes for reviewers

The Reproduce tab emits **runnable** `metafor` R: `escalc()` is called with explicit
measure-specific arguments (`ai/bi/ci/di` or `m1i/sd1i/…`), hazard ratios are pooled via
`log(HR)` + variance (no invalid escalc measure), the prediction interval is computed
explicitly as `t_{k-1} · √(τ²+SE²)`, and ratio measures are back-transformed with `exp()`.
DerSimonian-Laird at k<10 surfaces a warning. The embedded engines run in a `sandbox`ed
iframe; the tab widget is fully keyboard-navigable (arrow/Home/End, roving tabindex).
