#!/usr/bin/env python
"""Generate data/ma4.js from the real Pairwise70 'ma4' CSVs.

Source of truth (read-only, never modified):
  <src>/ma4_results_pairwise70.csv     -> a worked forest example (CD000028_pub4 outcomes)
  <src>/ma4_metafor_validation.csv     -> engine-vs-metafor agreement across reviews

The shipped data file (data/ma4.js) contains ONLY numbers transcribed from those CSVs,
so the Story forest and Benchmark agreement charts use real, validated data.

Usage:
  python tools/build_ma4_data.py [--src C:/Projects/Pairwise70/analysis]
Fails closed if the source CSVs are missing.
"""
import argparse
import csv
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = Path(r"C:\Projects\Pairwise70\analysis")
FOREST_REVIEW = "CD000028_pub4"   # ACE-inhibitor review: 6 logRR outcomes, all REML-validated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC), help="dir holding the ma4_*.csv files")
    args = ap.parse_args()
    src = Path(args.src)
    res = src / "ma4_results_pairwise70.csv"
    val = src / "ma4_metafor_validation.csv"
    for f in (res, val):
        if not f.is_file():
            print(f"FATAL: missing source CSV {f}\n"
                  f"Pass --src <dir> pointing at the Pairwise70 analysis folder.")
            sys.exit(2)

    # Forest: pooled logRR + SE for each outcome of one real review
    forest = []
    with res.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["review_id"] == FOREST_REVIEW and row["effect_type"] == "logRR":
                forest.append({
                    "label": row["analysis_name"],
                    "theta": float(row["theta"]),   # logRR
                    "sigma": float(row["sigma"]),    # SE(logRR)
                    "k": int(row["k"]),
                })

    # Agreement: ma4 engine vs metafor pooled estimate, per review
    agree, max_t, max_s = [], 0.0, 0.0
    with val.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                ma4, mf = float(row["ma4_theta"]), float(row["mf_theta"])
                td, sd = abs(float(row["theta_diff"])), abs(float(row["se_diff"]))
            except (ValueError, KeyError):
                continue
            agree.append({"x": round(mf, 6), "y": round(ma4, 6), "diff": td})
            max_t, max_s = max(max_t, td), max(max_s, sd)

    data = {
        "forestReview": FOREST_REVIEW,
        "forest": forest,
        "agreement": agree,
        "summary": {
            "nReviews": len(agree),
            "maxAbsThetaDiff": max_t,
            "maxAbsSeDiff": max_s,
            "oracle": "metafor REML",
        },
    }
    out = ROOT / "data" / "ma4.js"
    out.parent.mkdir(exist_ok=True)
    body = ("/* GENERATED from Pairwise70 ma4_*.csv by tools/build_ma4_data.py - real values only */\n"
            "window.PW70_MA4 = " + json.dumps(data, indent=2) + ";\n")
    out.write_text(body, encoding="utf-8")
    print(f"wrote {out} : {len(forest)} forest rows, {len(agree)} agreement points, "
          f"max|Δθ|={max_t:.2e}")


if __name__ == "__main__":
    main()
