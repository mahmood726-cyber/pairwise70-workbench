/* GENERATED from projects.json by tests/build_catalog.py - DO NOT EDIT BY HAND */
window.PW70_CATALOG = {
  "schema": "pairwise70-workbench/catalog@1",
  "generatedNote": "Descriptions taken verbatim/condensed from each repo's README; no marketing added. Update when repos change.",
  "projects": [
    {
      "id": "pairwisepro-v3",
      "name": "PairwisePro v3.0 (advanced)",
      "kind": "engine",
      "embed": "apps/PairwisePro-v3.0-advanced.html",
      "repo": "https://github.com/mahmood726-cyber/truthcert-pairwisepro-v2.git",
      "pages": null,
      "summary": "12-tab in-browser pairwise meta-analysis workbench: data import, pooled effect, heterogeneity, prediction intervals, Bayesian MA, bias/funnel, clinical decision, multi-outcome, validation, and R-code export.",
      "analysisTypes": [
        "pooling-OR-RR-SMD",
        "heterogeneity",
        "prediction-interval",
        "bayesian",
        "publication-bias",
        "clinical-decision",
        "multi-outcome",
        "tau2-estimators"
      ],
      "online": "Charts use Plotly via CDN; statistics run offline."
    },
    {
      "id": "mafi-calculator",
      "name": "MAFI Calculator (Meta-Analysis Fragility Index)",
      "kind": "engine",
      "embed": "apps/MAFI-Calculator-Complete.html",
      "repo": "https://github.com/mahmood726-cyber/Pairwise70.git",
      "pages": null,
      "summary": "Computes the Meta-Analysis Fragility Index — how many event reassignments flip a pooled significance verdict. Shipped alongside the Pairwise70 dataset; F1000 software-tool submission.",
      "analysisTypes": [
        "fragility-index",
        "pooling-OR-RR"
      ],
      "online": null
    },
    {
      "id": "pairwise70-dataset",
      "name": "Pairwise70 dataset (Cochrane corpus)",
      "kind": "dataset",
      "embed": null,
      "repo": "https://github.com/mahmood726-cyber/Pairwise70.git",
      "pages": null,
      "summary": "R data package: 501 systematically extracted pairwise meta-analysis datasets from Cochrane reviews (~50,000+ studies; 7,545 MAs). The shared corpus the rest of the family analyses.",
      "analysisTypes": [
        "dataset"
      ],
      "online": null
    },
    {
      "id": "repro-floor-atlas",
      "name": "Reproduction-Floor Atlas",
      "kind": "atlas",
      "embed": null,
      "repo": "https://github.com/mahmood726-cyber/repro-floor-atlas.git",
      "pages": "https://mahmood726-cyber.github.io/repro-floor-atlas/",
      "summary": "Measures whether Cochrane MAs publish results reproducible to claimed precision. Re-pooling at published precision yields |delta| > 0.005 in 14.3% of 7,545 MAs (Scenario B). Tier 1 / shipped, live dashboard.",
      "analysisTypes": [
        "reproduction-floor",
        "re-pooling"
      ],
      "online": "Live Pages dashboard."
    },
    {
      "id": "grma",
      "name": "GRMA — Grey Relational Meta-Analysis",
      "kind": "estimator",
      "embed": null,
      "repo": "https://github.com/mahmood726-cyber/grma.git",
      "pages": null,
      "summary": "Robust pooling estimator using grey-relational similarity in (effect, log-precision) space with a Tukey bisquare redescending guard and BCa bootstrap inference. Includes a pairwise70 benchmark harness.",
      "analysisTypes": [
        "robust-pooling",
        "bootstrap",
        "pairwise70-benchmark"
      ],
      "online": null
    },
    {
      "id": "gwam",
      "name": "GWAM — Ghost-Weighted Aggregate Meta-analysis",
      "kind": "estimator",
      "embed": null,
      "repo": "https://github.com/mahmood726-cyber/gwam.git",
      "pages": null,
      "summary": "Reproducible GWAM pipeline over ClinicalTrials.gov registry data: pulls completed trials, classifies publication linkage from CT.gov reference types, and weights for unpublished ('ghost') evidence. Includes a pairwise70 benchmark.",
      "analysisTypes": [
        "ghost-weighting",
        "publication-linkage",
        "pairwise70-benchmark"
      ],
      "online": "Pipeline pulls CT.gov data when run."
    },
    {
      "id": "miii-786",
      "name": "786-MIII Meta-analysis (Masroor)",
      "kind": "collection",
      "embed": null,
      "repo": "https://github.com/mahmood726-cyber/786-MIII-Meta-analysis.git",
      "pages": null,
      "summary": "R/Shiny source collection: pairwise OR, pairwise SMD, and RROR / annualised-rate meta-analysis tooling.",
      "analysisTypes": [
        "pooling-OR",
        "pooling-SMD",
        "RROR",
        "NMA"
      ],
      "online": null
    }
  ],
  "benchmark": {
    "name": "pairwise70 benchmark",
    "corpus": "Pairwise70 (501 reviews / 7,545 MAs)",
    "description": "Cross-engine validation harness: in-browser / Python / R estimators are compared against an R oracle (metafor/meta) over the Pairwise70 corpus. Present in grma, gwam, and pipeline_pairwise70.R across autograde-tool, evidencehalflife, metarep.",
    "harnesses": [
      "grma/run_pairwise70_benchmark.py",
      "pipeline_pairwise70.R"
    ]
  }
};
