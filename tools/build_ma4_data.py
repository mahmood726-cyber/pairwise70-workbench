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
SUBGROUP_REVIEW = "CD000402_pub5"    # unopposed-estrogen review: clean dose-response subgroups
SUBGROUP_NAME = "Endometrial hyperplasia at 1 year"
SUBGROUP_LEVELS = ["Low-dose estrogen", "Moderate-dose estrogen", "High-dose estrogen"]


def read_subgroup(rda_dir):
    """Real dose-response subgroup forest: pool each estrogen-dose stratum (RR)."""
    try:
        import math
        import pyreadr
    except ImportError:
        return None
    f = Path(rda_dir) / (SUBGROUP_REVIEW + "_data.rda")
    if not f.is_file():
        return None
    a = next(iter(pyreadr.read_r(str(f)).values()))
    a = a[a["Analysis.name"] == SUBGROUP_NAME]
    groups = []
    for s in SUBGROUP_LEVELS:
        r = a[(a["Subgroup"] == s) & a["Study"].notna() & a["Mean"].notna()
              & a["CI.start"].notna() & a["CI.end"].notna()]
        yv, vv = [], []
        for _, row in r.iterrows():
            m, lo, hi = float(row["Mean"]), float(row["CI.start"]), float(row["CI.end"])
            if m > 0 and lo > 0 and hi > lo:
                yv.append(math.log(m))
                vv.append(((math.log(hi) - math.log(lo)) / (2 * 1.959964)) ** 2)
        if len(yv) < 2:
            continue
        mu, se, _, _ = _pool(yv, vv)
        groups.append({"label": s.replace(" estrogen", ""), "k": len(yv),
                       "est": round(math.exp(mu), 3),
                       "lo": round(math.exp(mu - 1.959964 * se), 3),
                       "hi": round(math.exp(mu + 1.959964 * se), 3)})
    if len(groups) < 2:
        return None
    return {"review": SUBGROUP_REVIEW, "analysis": SUBGROUP_NAME, "measure": "RR", "groups": groups}


def compute_bayes(points, prior_tau_sd=0.5):
    """Bayesian random-effects pool via 2-D grid approximation over (mu, tau).
    Flat prior on mu, Half-Normal(0, prior_tau_sd) on tau. Returns posterior density
    of the pooled RR + 95% credible interval. Deterministic; documented prior."""
    import math
    yv = [p["x"] for p in points]
    vv = [p["se"] ** 2 for p in points]
    mus = [-0.45 + 0.9 * i / 199 for i in range(200)]          # logRR support
    taus = [0.5 * j / 79 for j in range(80)]                   # tau in [0, 0.5]
    grid = [[0.0] * len(taus) for _ in range(len(mus))]
    for ti, tau in enumerate(taus):
        lp_tau = -(tau * tau) / (2 * prior_tau_sd * prior_tau_sd)   # half-normal (tau >= 0)
        s2 = [v + tau * tau for v in vv]
        const = lp_tau - 0.5 * sum(math.log(2 * math.pi * s) for s in s2)
        for mi, mu in enumerate(mus):
            grid[mi][ti] = const - 0.5 * sum((y - mu) ** 2 / s for y, s in zip(yv, s2))
    mx = max(max(row) for row in grid)
    Z = 0.0
    for mi in range(len(mus)):
        for ti in range(len(taus)):
            grid[mi][ti] = math.exp(grid[mi][ti] - mx)
            Z += grid[mi][ti]
    pmu = [sum(grid[mi]) / Z for mi in range(len(mus))]         # marginal posterior of mu
    cum, c = [], 0.0
    for w in pmu:
        c += w
        cum.append(c)
    def q(p):
        for mi in range(len(mus)):
            if cum[mi] >= p:
                return mus[mi]
        return mus[-1]
    mmean = sum(m * w for m, w in zip(mus, pmu))
    dmu = mus[1] - mus[0]
    rr = [math.exp(m) for m in mus]
    dens = [pmu[mi] / dmu / rr[mi] for mi in range(len(mus))]   # density in RR space (Jacobian)
    return {"grid": [round(r, 4) for r in rr], "density": [round(d, 4) for d in dens],
            "est": round(math.exp(mmean), 4),
            "crI": [round(math.exp(q(0.025)), 4), round(math.exp(q(0.975)), 4)],
            "prior": "tau ~ Half-Normal(0, 0.5), flat mu"}


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


REVIEWS = ["CD000028_pub4", "CD000219_pub5", "CD001155_pub3", "CD000478_pub5", "CD000547_pub3"]
REVIEW_LABELS = {
    "CD000028_pub4": "Antihypertensives in the elderly",
    "CD000219_pub5": "Antibiotics for acute otitis media",
    "CD001155_pub3": "Bisphosphonates / fracture prevention",
    "CD000478_pub5": "Maintenance of remission (IBD)",
    "CD000547_pub3": "Myomectomy / fibroid surgery",
}


def _points_for(df, analysis_name):
    """Overall (no-subgroup) per-study logRR + SE for one outcome."""
    import math
    import re
    sub = df[(df["Analysis.name"] == analysis_name) & df["Study"].notna()
             & df["Mean"].notna() & df["CI.start"].notna() & df["CI.end"].notna()]
    seen, pts = set(), []
    for _, r in sub.iterrows():
        m, lo, hi = float(r["Mean"]), float(r["CI.start"]), float(r["CI.end"])
        study = str(r["Study"]).strip()
        # one point per distinct trial (some outcomes list every study only under subgroups)
        if not (m > 0 and lo > 0 and hi > lo) or study in seen:
            continue
        seen.add(study)
        yr = r["Study.year"]
        year = int(yr) if (yr == yr and yr is not None) else (
            int(re.search(r"(19|20)\d{2}", study).group(0)) if re.search(r"(19|20)\d{2}", study) else None)
        pts.append({"study": study, "year": year, "x": round(math.log(m), 6),
                    "se": round((math.log(hi) - math.log(lo)) / (2 * 1.959964), 6)})
    return pts


def build_reviews(src, rda_dir):
    """Forest of outcomes + one representative outcome's per-study points, per review."""
    import csv as _csv
    try:
        import pyreadr
    except ImportError:
        return None
    by_rev = {}
    with (src / "ma4_results_pairwise70.csv").open(encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            if row["effect_type"] == "logRR" and row["review_id"] in REVIEWS:
                by_rev.setdefault(row["review_id"], []).append(row)
    out = []
    for rid in REVIEWS:
        rows = by_rev.get(rid, [])
        f = Path(rda_dir) / (rid + "_data.rda")
        if not rows or not f.is_file():
            continue
        forest = [{"label": r["analysis_name"], "theta": float(r["theta"]),
                   "sigma": float(r["sigma"]), "k": int(r["k"])} for r in rows]
        df = next(iter(pyreadr.read_r(str(f)).values()))
        rep_row = max(rows, key=lambda r: int(r["k"]))     # outcome with the most trials
        pts = _points_for(df, rep_row["analysis_name"])
        if len(pts) < 3:
            continue
        theta, sigma, tau, k = (float(rep_row["theta"]), float(rep_row["sigma"]),
                                float(rep_row["tau"]), len(pts))
        out.append({"id": rid, "label": REVIEW_LABELS.get(rid, rid),
                    "forest": forest,
                    "rep": {"name": rep_row["analysis_name"], "k": k, "points": pts,
                            "theta": theta, "sigma": sigma, "tau": tau},
                    # full deep-dive precomputed per review (drives the interactive explorer)
                    "interval": compute_interval(theta, sigma, tau, k),
                    "loo": compute_loo(pts),
                    "cumulative": compute_cumulative(pts),
                    "gosh": compute_gosh(pts),
                    "bayes": compute_bayes(pts)})
    return out or None


def compute_estimators(points):
    """Same data, three models: fixed-effect, DerSimonian-Laird, Paule-Mandel.
    Shows how the 'answer' shifts with estimator choice."""
    import math
    yv = [p["x"] for p in points]
    vv = [p["se"] ** 2 for p in points]
    m = len(yv)

    def re_pool(tau2):
        ws = [1.0 / (v + tau2) for v in vv]
        sws = sum(ws)
        mu = sum(w * y for w, y in zip(ws, yv)) / sws
        return mu, math.sqrt(1.0 / sws)
    # fixed effect
    mu_fe, se_fe = re_pool(0.0)
    # DL
    wf = [1.0 / v for v in vv]
    sw = sum(wf)
    ybar = sum(w * y for w, y in zip(wf, yv)) / sw
    Q = sum(w * (y - ybar) ** 2 for w, y in zip(wf, yv))
    C = sw - sum(w * w for w in wf) / sw
    tau2_dl = max(0.0, (Q - (m - 1)) / C) if C > 0 else 0.0
    mu_dl, se_dl = re_pool(tau2_dl)
    # Paule-Mandel (iterate so sum wi*(yi-ybar)^2 = m-1)
    tau2_pm = tau2_dl
    for _ in range(100):
        ws = [1.0 / (v + tau2_pm) for v in vv]
        sws = sum(ws)
        mb = sum(w * y for w, y in zip(ws, yv)) / sws
        F = sum(w * (y - mb) ** 2 for w, y in zip(ws, yv)) - (m - 1)
        dF = -sum((w ** 2) * (y - mb) ** 2 for w, y in zip(ws, yv))
        if abs(dF) < 1e-12:
            break
        step = F / dF
        tau2_pm = max(0.0, tau2_pm - step)
        if abs(step) < 1e-10:
            break

    def row(label, mu, se, tau2):
        return {"label": label, "est": round(math.exp(mu), 4),
                "lo": round(math.exp(mu - 1.959964 * se), 4),
                "hi": round(math.exp(mu + 1.959964 * se), 4),
                "tau2": round(tau2, 5)}
    return [row("Fixed-effect", mu_fe, se_fe, 0.0),
            row("Random (DL)", mu_dl, se_dl, tau2_dl),
            row("Random (Paule-Mandel)", *re_pool(tau2_pm), tau2_pm)]


PUBBIAS_REVIEW = "CD001396_pub4"
PUBBIAS_OUTCOME = "Response rates"


def read_pubbias(rda_dir):
    """A real outcome with funnel asymmetry: Egger + Duval-Tweedie trim-and-fill.
    Shows how much a small-study/publication-bias adjustment moves the pooled RR."""
    try:
        import math
        import pyreadr
    except ImportError:
        return None
    f = Path(rda_dir) / (PUBBIAS_REVIEW + "_data.rda")
    if not f.is_file():
        return None
    df = next(iter(pyreadr.read_r(str(f)).values()))
    pts = _points_for(df, PUBBIAS_OUTCOME)
    if len(pts) < 10:
        return None
    ys = [p["x"] for p in pts]
    vs = [p["se"] ** 2 for p in pts]
    n = len(ys)

    def dl(yy, vv):
        wf = [1.0 / v for v in vv]
        sw = sum(wf)
        yb = sum(w * y for w, y in zip(wf, yy)) / sw
        Q = sum(w * (y - yb) ** 2 for w, y in zip(wf, yy))
        d = len(yy) - 1
        C = sw - sum(w * w for w in wf) / sw
        t2 = max(0.0, (Q - d) / C) if C > 0 else 0.0
        ws = [1.0 / (v + t2) for v in vv]
        sws = sum(ws)
        return sum(w * y for w, y in zip(ws, yy)) / sws, math.sqrt(1.0 / sws)

    # Duval & Tweedie L0 trim-and-fill (RE centering)
    mu, _ = dl(ys, vs)
    k0 = 0
    for _ in range(50):
        order = sorted(range(n), key=lambda i: abs(ys[i] - mu))
        signs = [1 if ys[order[r]] > mu else -1 for r in range(n)]
        Tn = sum((r + 1) for r in range(n) if signs[r] > 0)
        L0 = (4 * Tn - n * (n + 1)) / (2 * n - 1)
        k = max(0, int(round(L0)))
        keep = order[:n - k]
        muN, _ = dl([ys[i] for i in keep], [vs[i] for i in keep])
        if k == k0 and abs(muN - mu) < 1e-9:
            mu, k0 = muN, k
            break
        mu, k0 = muN, k
    ext = sorted(range(n), key=lambda i: -abs(ys[i] - mu))[:k0]
    imputed = [{"x": round(2 * mu - ys[i], 6), "se": round(math.sqrt(vs[i]), 6)} for i in ext]
    mu0, se0 = dl(ys, vs)
    ys2 = ys + [2 * mu - ys[i] for i in ext]
    vs2 = vs + [vs[i] for i in ext]
    muA, seA = dl(ys2, vs2)
    eg = compute_egger(pts)

    def rr(m, s):
        return {"est": round(math.exp(m), 3), "lo": round(math.exp(m - 1.959964 * s), 3),
                "hi": round(math.exp(m + 1.959964 * s), 3)}
    return {"review": PUBBIAS_REVIEW, "outcome": PUBBIAS_OUTCOME, "k": n, "k0": k0,
            "egger": eg, "pooledLogOrig": round(mu0, 6),
            "points": [{"study": p["study"], "x": p["x"], "se": p["se"]} for p in pts],
            "imputed": imputed, "original": rr(mu0, se0), "adjusted": rr(muA, seA)}


def compute_egger(points):
    """Egger's regression test for small-study effects (intercept != 0)."""
    import math
    snd = [p["x"] / p["se"] for p in points]            # standard normal deviate
    prec = [1.0 / p["se"] for p in points]              # precision
    n = len(points)
    mx = sum(prec) / n
    my = sum(snd) / n
    sxx = sum((x - mx) ** 2 for x in prec)
    sxy = sum((x - mx) * (y - my) for x, y in zip(prec, snd))
    if sxx == 0:
        return None
    slope = sxy / sxx
    intercept = my - slope * mx
    resid = [y - (intercept + slope * x) for x, y in zip(prec, snd)]
    s2 = sum(r * r for r in resid) / (n - 2)
    se_int = math.sqrt(s2 * (1.0 / n + mx * mx / sxx))
    t = intercept / se_int if se_int > 0 else 0.0
    # two-sided p via survival of |t| under t_{n-2}, small-table normal approx
    p = math.erfc(abs(t) / math.sqrt(2))               # normal approx (k>=10)
    return {"intercept": round(intercept, 3), "t": round(t, 2), "p": round(p, 3),
            "k": n, "note": "normal approx; Egger has low power for k<10"}


def _histogram(values, edges, labels):
    """Bucket counts for renderBars. edges define right-open bins; last is open-ended."""
    counts = [0] * len(labels)
    for v in values:
        for i in range(len(labels)):
            if v < edges[i + 1]:
                counts[i] += 1
                break
    return [{"label": labels[i], "value": counts[i]} for i in range(len(labels))]


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
    forest, taus, ks = [], [], []
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
            try:
                ks.append(int(row["k"]))
            except (ValueError, KeyError):
                pass
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

    # Real dose-response subgroup forest (different review) + Bayesian posterior
    subgroup = read_subgroup(args.rda)
    bayes = compute_bayes(funnel["points"]) if funnel else None

    # Multi-review set for the interactive dropdown
    reviews = build_reviews(src, Path(args.rda))

    # "Issues with Cochrane MAs" — real corpus-computed evidence
    small_k = sum(1 for k in ks if k < 10)
    issues = {
        "kHist": _histogram(ks, [1, 2, 3, 5, 10, 20, 50, 10 ** 9],
                            ["1", "2", "3-4", "5-9", "10-19", "20-49", "50+"]),
        "kSmallFrac": round(small_k / len(ks), 3) if ks else None,
        "kN": len(ks),
        "estimators": compute_estimators(funnel["points"]) if funnel else None,
        "egger": compute_egger(funnel["points"]) if funnel else None,
        "pubbias": read_pubbias(args.rda),
    }

    data = {
        "forestReview": FOREST_REVIEW,
        "forest": forest,
        "funnel": funnel,
        "loo": loo,
        "gosh": gosh,
        "cumulative": cumulative,
        "interval": interval,
        "tauDensity": tau_density,
        "subgroup": subgroup,
        "bayes": bayes,
        "reviews": reviews,
        "issues": issues,
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
