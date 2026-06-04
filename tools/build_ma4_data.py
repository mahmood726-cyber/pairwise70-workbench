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
DEFAULT_RDA = Path(r"C:\Projects\Pairwise70\data")
FOREST_REVIEW = "CD000028_pub4"      # antihypertensive review: 6 logRR outcomes, all REML-validated
FUNNEL_NAME = "All-cause mortality"  # one outcome; Analysis.group 1 = overall (k=13), groups 2-3 = age subgroups


def read_funnel(rda_dir, pooled_logrr):
    """Per-study logRR + SE for one analysis, read straight from the Pairwise70 .rda
    via pyreadr (no R needed). Returns None if pyreadr or the file is unavailable."""
    try:
        import math
        import pyreadr
    except ImportError:
        print("note: pyreadr not installed; skipping funnel (forest + agreement still built)")
        return None
    f = Path(rda_dir) / (FOREST_REVIEW + "_data.rda")
    if not f.is_file():
        print(f"note: {f} missing; skipping funnel")
        return None
    import re
    df = next(iter(pyreadr.read_r(str(f)).values()))
    # group 1 = the overall pooled set (k=13); groups 2-3 are mutually-exclusive age subgroups
    sub = df[(df["Analysis.name"] == FUNNEL_NAME) & (df["Analysis.group"] == 1)
             & df["Study"].notna() & df["Mean"].notna()
             & df["CI.start"].notna() & df["CI.end"].notna()]
    pts = []
    for _, r in sub.iterrows():
        m, lo, hi = float(r["Mean"]), float(r["CI.start"]), float(r["CI.end"])
        if not (m > 0 and lo > 0 and hi > lo):
            continue
        x = math.log(m)                                  # per-study logRR
        se = (math.log(hi) - math.log(lo)) / (2 * 1.959964)
        study = str(r["Study"]).strip()
        yr = r["Study.year"]
        if yr == yr and yr is not None:                  # not NaN
            year = int(yr)
        else:
            mt = re.search(r"(19|20)\d{2}", study)        # fall back to the year in the name
            year = int(mt.group(0)) if mt else None
        pts.append({"study": study, "year": year, "x": round(x, 6), "se": round(se, 6)})
    if not pts:
        return None
    return {"analysis": "All-cause mortality", "measure": "logRR",
            "pooled": round(pooled_logrr, 6), "points": pts}


def _pool(yv, vv):
    """DerSimonian-Laird random-effects pool of (yi, vi). Returns mu, se, tau2, I2(%)."""
    import math
    m = len(yv)
    wf = [1.0 / v for v in vv]
    sw = sum(wf)
    ybar = sum(w * y for w, y in zip(wf, yv)) / sw
    Q = sum(w * (y - ybar) ** 2 for w, y in zip(wf, yv))
    df = m - 1
    C = sw - sum(w * w for w in wf) / sw
    tau2 = max(0.0, (Q - df) / C) if C > 0 else 0.0
    ws = [1.0 / (v + tau2) for v in vv]
    sws = sum(ws)
    mu = sum(w * y for w, y in zip(ws, yv)) / sws
    se = math.sqrt(1.0 / sws)
    i2 = max(0.0, (Q - df) / Q) * 100.0 if Q > 0 else 0.0
    return mu, se, tau2, i2


def compute_loo(points):
    """Leave-one-out random-effects re-pool of the real per-study (logRR, SE)."""
    import math
    yv = [p["x"] for p in points]
    vv = [p["se"] ** 2 for p in points]
    mu0, se0, _, _ = _pool(yv, vv)
    rows = []
    for i, p in enumerate(points):
        yy = yv[:i] + yv[i + 1:]
        vv2 = vv[:i] + vv[i + 1:]
        mu, se, _, _ = _pool(yy, vv2)
        rows.append({"label": "− " + p["study"],
                     "est": round(math.exp(mu), 4),
                     "lo": round(math.exp(mu - 1.959964 * se), 4),
                     "hi": round(math.exp(mu + 1.959964 * se), 4)})
    return {"overall": round(math.exp(mu0), 4), "rows": rows}


def compute_cumulative(points):
    """Cumulative random-effects meta-analysis, studies entered by year."""
    import math
    ordered = sorted([p for p in points if p.get("year")], key=lambda p: p["year"])
    rows = []
    for i in range(len(ordered)):
        yv = [p["x"] for p in ordered[:i + 1]]
        vv = [p["se"] ** 2 for p in ordered[:i + 1]]
        mu, se, _, _ = _pool(yv, vv)
        p = ordered[i]
        rows.append({"label": "+ " + p["study"],
                     "est": round(math.exp(mu), 4),
                     "lo": round(math.exp(mu - 1.959964 * se), 4),
                     "hi": round(math.exp(mu + 1.959964 * se), 4)})
    final = rows[-1]["est"] if rows else None
    return {"overall": final, "rows": rows}


def compute_interval(theta, sigma, tau, k):
    """Pooled estimate with 95% CI and 95% prediction interval, back-transformed to RR.
    PI uses t_{k-1} * sqrt(tau^2 + SE^2) (Cochrane Handbook v6.5)."""
    import math
    # two-sided t critical value, df = k-1 (small-table lookup; df here is 12)
    tcrit = {1:12.706,2:4.303,3:3.182,4:2.776,5:2.571,6:2.447,7:2.365,8:2.306,9:2.262,
             10:2.228,11:2.201,12:2.179,13:2.160,14:2.145,15:2.131,20:2.086,30:2.042}.get(k-1, 1.96)
    ci = (math.exp(theta - 1.959964 * sigma), math.exp(theta + 1.959964 * sigma))
    pw = tcrit * math.sqrt(tau ** 2 + sigma ** 2)
    pi = (math.exp(theta - pw), math.exp(theta + pw))
    return {"est": round(math.exp(theta), 4), "ci": [round(ci[0], 4), round(ci[1], 4)],
            "pi": [round(pi[0], 4), round(pi[1], 4)], "k": k, "measure": "RR"}


def compute_density(values, n=80):
    """Gaussian-KDE of a list of values -> grid + density arrays for renderDensity."""
    import math
    vals = [v for v in values if v is not None and v == v]
    if len(vals) < 3:
        return None
    lo, hi = min(vals), max(vals)
    if hi <= lo:
        hi = lo + 1e-6
    mean = sum(vals) / len(vals)
    sd = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5 or (hi - lo) / 6 or 1e-6
    bw = 1.06 * sd * len(vals) ** (-0.2) or (hi - lo) / 20
    grid = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    dens = [sum(math.exp(-0.5 * ((g - v) / bw) ** 2) for v in vals) / (len(vals) * bw * math.sqrt(2 * math.pi))
            for g in grid]
    return {"grid": [round(g, 5) for g in grid], "density": [round(d, 5) for d in dens], "n": len(vals)}


def compute_gosh(points, cap=2500):
    """GOSH: fixed-effect pooled estimate vs I^2 over every >=2-study subset."""
    import math
    yv = [p["x"] for p in points]
    vv = [p["se"] ** 2 for p in points]
    m = len(points)
    allpts = []
    for mask in range(1, 1 << m):
        idx = [i for i in range(m) if mask & (1 << i)]
        if len(idx) < 2:
            continue
        yy = [yv[i] for i in idx]
        vv2 = [vv[i] for i in idx]
        wf = [1.0 / v for v in vv2]
        sw = sum(wf)
        ybar = sum(w * y for w, y in zip(wf, yy)) / sw          # fixed-effect estimate
        Q = sum(w * (y - ybar) ** 2 for w, y in zip(wf, yy))
        df = len(idx) - 1
        i2 = max(0.0, (Q - df) / Q) * 100.0 if Q > 0 else 0.0
        allpts.append({"x": round(math.exp(ybar), 4), "y": round(i2, 1)})
    total = len(allpts)
    if total > cap:                                              # deterministic systematic sample
        step = total / cap
        allpts = [allpts[int(i * step)] for i in range(cap)]
    return {"total": total, "shown": len(allpts), "points": allpts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC), help="dir holding the ma4_*.csv files")
    ap.add_argument("--rda", default=str(DEFAULT_RDA), help="dir holding the Pairwise70 *_data.rda files")
    args = ap.parse_args()
    src = Path(args.src)
    res = src / "ma4_results_pairwise70.csv"
    val = src / "ma4_metafor_validation.csv"
    for f in (res, val):
        if not f.is_file():
            print(f"FATAL: missing source CSV {f}\n"
                  f"Pass --src <dir> pointing at the Pairwise70 analysis folder.")
            sys.exit(2)

    # Forest: pooled logRR + SE for each outcome of one real review.
    # Also collect every logRR tau across the corpus sample for a heterogeneity density.
    forest, taus = [], []
    with res.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["effect_type"] != "logRR":
                continue
            try:
                tau = float(row["tau"])
            except (ValueError, KeyError):
                tau = None
            if tau is not None and tau > 1e-4:        # drop the ~6e-6 numeric-floor zeros
                taus.append(tau)
            if row["review_id"] == FOREST_REVIEW:
                forest.append({
                    "label": row["analysis_name"],
                    "theta": float(row["theta"]),     # logRR
                    "sigma": float(row["sigma"]),      # SE(logRR)
                    "tau": tau if tau is not None else 0.0,
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

    # Funnel: per-study logRR + SE for analysis 1 of the same review (real .rda)
    pooled1 = next((r["theta"] for r in forest if r["label"] == "All-cause mortality"), 0.0)
    funnel = read_funnel(args.rda, pooled1)

    # Leave-one-out + GOSH + cumulative from the real 13 per-study points
    loo = compute_loo(funnel["points"]) if funnel else None
    gosh = compute_gosh(funnel["points"]) if funnel else None
    cumulative = compute_cumulative(funnel["points"]) if funnel else None

    # Prediction interval for the all-cause-mortality outcome (real theta/sigma/tau/k)
    a1 = next((r for r in forest if r["label"] == "All-cause mortality"), None)
    interval = compute_interval(a1["theta"], a1["sigma"], a1["tau"], a1["k"]) if a1 else None

    # Heterogeneity density across the logRR corpus sample
    tau_density = compute_density(taus)

    data = {
        "forestReview": FOREST_REVIEW,
        "forest": forest,
        "funnel": funnel,
        "loo": loo,
        "gosh": gosh,
        "cumulative": cumulative,
        "interval": interval,
        "tauDensity": tau_density,
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
