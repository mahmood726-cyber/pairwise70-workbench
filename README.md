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

For the embedded engines' charts (Plotly), an internet connection is needed; all
hub-shell features and the statistics themselves run offline.

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
projects.json    # the project catalog (real metadata, no marketing)
apps/            # vendored HTML engines, byte-identical copies of the originals
  PairwisePro-v3.0-advanced.html
  MAFI-Calculator-Complete.html
docs/spec.md     # scope, portfolio recon (reused vs net-new), non-goals
tests/           # validate.py (structural) + smoke.py (headless browser)
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

Edit **both** `projects.json` (canonical data) **and** the inline `CATALOG` object in
`index.html` (so the hub works from `file://` without fetch). `tests/validate.py`
fails if the two drift apart.

## Tests

```
python tests/validate.py     # 31 structural checks
python tests/smoke.py         # 10 headless-browser checks (needs Chrome + selenium)
```

## Known limitations

- The vendored PairwisePro v3.0 engine loads Plotly + Google Fonts from CDN (inherited
  from the original app). Vendoring Plotly locally for a zero-network engine is a
  tracked follow-up.
- The catalog is duplicated (JSON + inline) for `file://` compatibility; a test guards
  against drift.

## License

MIT. Embedded engines retain their original licenses from their source repos.
