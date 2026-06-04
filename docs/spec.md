# Pairwise70 Workbench — Spec

## Purpose
A single offline program that (a) **shows** every Pairwise70-family project in one
gallery and (b) lets you **run / reproduce** every analysis type in one place, while
**leaving every individual repo untouched**. It is a hub shell that embeds the proven
HTML analysis engines and links the code/data repos.

## Decisions (confirmed with user 2026-06-04)
- **Architecture:** Hub + embedded engine. Tabs: `Projects | Analyze | Benchmark | Reproduce`.
- **Reproducibility bar (v1):** in-browser deterministic + exportable. Every run that
  the hub records carries inputs + model settings + seed + app version, and can export
  an `metafor` R snippet + a JSON run-record that re-creates it. No external runtime.
- **Offline:** the hub shell (`index.html`) ships zero external CDN. Embedded engines
  keep their existing dependencies (see Known limitations).

## Portfolio recon (rules: reused vs net-new)
Index source: `C:\Projects\projectindex-audit\agent-records\restart-manifest.json`
(top hit: `repro-floor-atlas`, Tier 1 / Shipped). On-disk sweep found ~15 pairwise
directories / 60+ artifacts. Families:

| Family | Repos / artifacts | Role here |
|---|---|---|
| PairwisePro app | `truthcert-pairwisepro-v2/PairwisePro-v3.0-advanced.html` (810 KB, 12 tabs), pairwiseai, htmlpairwise, truthcert1, HTML-Misc, Superhtml/superpairwise | **REUSED** — v3.0 vendored verbatim as the primary engine |
| MAFI | `Pairwise70/MAFI-Calculator-Complete.html` | **REUSED** — vendored verbatim as a second engine |
| Pairwise70 dataset | `Pairwise70` (R pkg, 501 reviews / 7545 MAs) | **LINKED** — gallery card + repo link |
| repro-floor-atlas | Tier 1 shipped, live Pages dashboard | **LINKED** — gallery card + Pages link |
| Robust estimators | `grma` (GRMA), `gwam` (GWAM) | **LINKED** — gallery cards |
| MIII Masroor | `786-MIII-Meta-analysis` (Pairwise OR / SMD / RROR) | **LINKED** — gallery card |

**Net-new** (this repo only): the hub shell `index.html`, the data-driven catalog
`projects.json`, the cross-project **Reproduce** cockpit (run-record schema + R export),
the structural test harness, and the offline iframe loader.

**Reused** (copied verbatim, originals untouched): the two HTML engines under `apps/`.

This blocks the "rewrite from scratch" anti-pattern: no statistical engine is
re-implemented here; the hub orchestrates existing, proven engines.

## Non-goals (v1)
- No edits to any source repo.
- No re-implementation of pooling math in the hub shell (engines own that).
- No R/Python oracle-parity assertions in v1 (deferred; user chose in-browser bar).
- Not necessarily single-*file* (it is a small single-*repo*: hub + vendored apps).

## Offline (resolved)
- Plotly v2.27.0 is vendored at `apps/vendor/plotly-2.27.0.min.js`; the engines' font
  CDN links were replaced with locally vendored woff2 + CSS under `assets/fonts/`. Both
  engines now load with **zero external references** (asserted by `tests/validate.py`,
  and proven offline by `tests/smoke.py` checking `typeof Plotly`).
- Catalog duplication removed: `projects.json` is the single source; `catalog.js` is
  generated from it (`tests/build_catalog.py`) and loaded via a `file://`-safe script
  tag. `validate.py` runs `--check` so the two cannot drift.
