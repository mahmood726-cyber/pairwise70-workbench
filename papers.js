/* E156 micro-papers for the Pairwise70 family.
   Bodies are the REAL text from each repo's e156-submission (verbatim, header stripped),
   except the Workbench capsule which describes this hub. No numbers invented here. */
window.PW70_PAPERS = [
  {
    id: "repro-floor-atlas",
    title: "Reproduction-Floor Atlas",
    type: "result",                 // structured S1-S7 results capsule
    estimand: "Proportion of Cochrane MAs with |Δ| > 0.005 under Scenario-B adaptive rounding.",
    repo: "https://github.com/mahmood726-cyber/repro-floor-atlas",
    pages: "https://mahmood726-cyber.github.io/repro-floor-atlas/",
    sentences: [
      "Can a Cochrane meta-analysis be reproduced to its published precision using only the per-trial numerics a reader extracts from the paper?",
      "Pairwise70 corpus: 595 Cochrane reviews comprising 7,545 meta-analyses spanning binary, continuous, and generic-inverse-variance outcomes, with trial-level inputs at machine precision.",
      "We re-pooled each MA at machine precision and after rounding per-trial inputs to Cochrane's adaptive precision plus fixed 1-3 dp.",
      "Across 7,545 Cochrane MAs, 14.3% had reproduction error |Δ| > 0.005 under forest-plot extraction; the failure rate was 12.9% for binary outcomes but 25-27% for continuous and GIV outcomes.",
      "The scaling relation |Δ| ~ 10^(-dp) held across binary, continuous, and GIV strata, and was stable under both raw-extraction and forest-plot framings.",
      "Published two-decimal-place precision in pooled effects exceeds the information content extractable per-trial; this is a structural limit, not a method flaw.",
      "Claim scope: aggregate-data reproduction with fixed-effect pooling; does not apply to individual-patient-data re-analysis or to random-effects estimators outside this simulation."
    ]
  },
  {
    id: "pairwise70-dataset",
    title: "Pairwise70: Standardized Dataset of 501 Cochrane Meta-Analyses",
    type: "protocol",
    estimand: "Fragility index",
    repo: "https://github.com/mahmood726-cyber/Pairwise70",
    body: "This protocol describes the planned evidence synthesis for Pairwise70: Standardized Dataset of 501 Cochrane Meta-Analyses, targeting transparent, reproducible estimation of Fragility index in a versioned analytical workflow. Eligible studies include Cochrane systematic reviews and randomised trials reporting the primary outcome, with no restrictions on publication year, language, geography, or sample size. Searches will cover the Cochrane Library, PubMed, and Embase using structured search terms, reference-list screening, and duplicate full-text review before extraction. The primary analysis will estimate Fragility index using restricted maximum likelihood random-effects meta-analysis, reporting 95 percent confidence intervals, prediction intervals, and prespecified model checks. Heterogeneity will be summarised using I-squared and tau-squared, with sensitivity analyses across variance estimators, exclusion scenarios, and leave-one-out patterns. Analysis code will be versioned and archived, and reporting will follow PRISMA 2020 guidance to support independent verification and reuse. Anticipated limitations include publication bias, clinical heterogeneity, sparse data in some settings, and the constraints of aggregate-level evidence synthesis."
  },
  {
    id: "grma",
    title: "GRMA: Grey Relational Meta-Analysis with Redescending Effect Guard",
    type: "protocol",
    estimand: "Bias reduction (percent)",
    repo: "https://github.com/mahmood726-cyber/grma",
    body: "This protocol describes the planned evidence synthesis for Grey Relational Meta-Analysis: A Robust Pooling Method, targeting transparent, reproducible estimation of Bias reduction (percent) in a versioned workflow. Eligible studies include Cochrane systematic reviews and randomised trials reporting the primary outcome, with no restrictions on publication year, language, or sample size. Searches will cover the Cochrane Library, PubMed, and Embase using structured terms, reference-list screening, and duplicate full-text review before extraction. The primary analysis will estimate Bias reduction (percent) using restricted maximum likelihood random-effects meta-analysis, reporting 95 percent confidence intervals, prediction intervals, and prespecified model checks. Heterogeneity will be summarised using I-squared and tau-squared, with sensitivity analyses across variance estimators, exclusion scenarios, and leave-one-out patterns. Analysis code will be versioned and archived, and reporting will follow PRISMA 2020 guidance to support independent verification and reuse. Anticipated limitations include publication bias, clinical heterogeneity, sparse data in some settings, and the constraints of aggregate-level evidence synthesis."
  },
  {
    id: "gwam",
    title: "GWAM: Ghost-Weighted Aggregate Meta-Analysis",
    type: "protocol",
    estimand: "Integrity ratio (lambda)",
    repo: "https://github.com/mahmood726-cyber/gwam",
    body: "This protocol describes the planned evidence synthesis for GWAM: Ghost-Weighted Aggregate Meta-Analysis for Registry-Based Publication Bias, targeting transparent, reproducible estimation of Integrity ratio (lambda) in a versioned workflow. Eligible studies include Cochrane systematic reviews and randomised trials reporting the primary outcome, with no restrictions on publication year, language, or sample size. Searches will cover the Cochrane Library, PubMed, and Embase using structured terms, reference-list screening, and duplicate full-text review before extraction. The primary analysis will estimate Integrity ratio (lambda) using restricted maximum likelihood random-effects meta-analysis, reporting 95 percent confidence intervals, prediction intervals, and prespecified model checks. Heterogeneity will be summarised using I-squared and tau-squared, with sensitivity analyses across variance estimators, exclusion scenarios, and leave-one-out patterns. Analysis code will be versioned and archived, and reporting will follow PRISMA 2020 guidance to support independent verification and reuse. Anticipated limitations include publication bias, clinical heterogeneity, sparse data in some settings, and the constraints of aggregate-level evidence synthesis."
  },
  {
    id: "pairwise70-workbench",
    title: "Pairwise70 Workbench (tool capsule)",
    type: "tool",
    estimand: "Unification: one offline program for the Pairwise70 family.",
    repo: "https://github.com/mahmood726-cyber/pairwise70-workbench",
    body: "The Pairwise70 Workbench is a single offline program that gathers the Pairwise70 family of meta-analysis projects into one place without altering any of them. It shows every project in a gallery, embeds the analysis engines so they run live in the browser, and narrates the family's central finding with charts drawn from real recorded data. Each analysis can be captured as a manifest carrying its inputs, model, seed, and a digest, and exported as a runnable metafor script so the numbers can be regenerated offline. Plotly, the web fonts, and the chart kit are vendored locally, so the hub and its engines work with no network connection. The program adds no statistical claims of its own; it orchestrates the existing, separately published tools and links back to each source repository."
  }
];
