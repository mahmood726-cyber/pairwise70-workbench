#!/usr/bin/env python
"""Structural validator for the Pairwise70 Workbench hub.

Checks the shipped hub (index.html + projects.json + vendored apps) for the
HTML-app safety invariants in the user's rules: no literal </script> leakage,
no unpopulated placeholders, no hardcoded local paths, catalog consistency,
and that every embedded engine actually exists on disk.

Run from repo root:  python tests/validate.py
"""
import io
import json
import re
import sys
from pathlib import Path

# UTF-8 stdout on Windows cp1252 consoles (rules: Data Handling)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
FAILS, CHECKS = [], 0


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  [PASS] {msg}")
    else:
        print(f"  [FAIL] {msg}")
        FAILS.append(msg)


def main():
    index = ROOT / "index.html"
    catalog = ROOT / "projects.json"

    print("== files exist ==")
    check(index.is_file(), "index.html present")
    check(catalog.is_file(), "projects.json present")
    if not index.is_file() or not catalog.is_file():
        return finish()

    html = index.read_text(encoding="utf-8")
    cat = json.loads(catalog.read_text(encoding="utf-8"))

    print("== HTML safety invariants ==")
    # Script tags must balance; any extra </script> means template-literal leakage.
    opens = len(re.findall(r"<script[\s>]", html))
    closes = html.count("</script>")
    check(opens == closes, f"<script> tags balanced ({opens} open / {closes} close; no template leakage)")
    for tok in ("{{", "REPLACE_ME", "__PLACEHOLDER__", "TODO_FILL"):
        check(tok not in html, f"no unpopulated placeholder token '{tok}'")
    # No hardcoded local/absolute paths in the shipped hub.
    for bad in (r"C:\\", "C:/Users", "/c/Projects", "/home/", "/Users/"):
        check(bad not in html, f"no hardcoded local path '{bad}' in index.html")
        check(bad not in catalog.read_text(encoding="utf-8"), f"no hardcoded local path '{bad}' in projects.json")
    # Offline: the hub shell must not load external scripts/styles itself.
    ext = re.findall(r'src="https?://[^"]+|<link[^>]+href="https?://[^"]+', html)
    check(len(ext) == 0, f"hub shell loads zero external resources (found {len(ext)})")
    check("og:title" in html and "og:description" in html, "Open Graph meta tags present")

    print("== catalog validity ==")
    check(cat.get("schema", "").startswith("pairwise70-workbench/catalog"), "catalog schema tag present")
    projects = cat.get("projects", [])
    check(len(projects) >= 5, f"catalog has >=5 projects (has {len(projects)})")
    json_ids = {p["id"] for p in projects}

    print("== embedded engines exist on disk ==")
    for p in projects:
        if p.get("kind") == "engine":
            embed = ROOT / p["embed"]
            check(embed.is_file() and embed.stat().st_size > 0,
                  f"engine '{p['id']}' -> {p['embed']} exists and non-empty")

    print("== single-source catalog (no inline duplication) ==")
    check("const CATALOG = window.PW70_CATALOG" in html,
          "hub reads catalog from generated catalog.js (no inline copy)")
    check('<script src="catalog.js">' in html, "index.html loads catalog.js via script tag")
    check("const CATALOG = {" not in html, "no inline CATALOG object literal remains")
    # catalog.js must be in sync with projects.json (drift impossible).
    # Run as a subprocess so build_catalog's stdout reassignment can't clobber ours.
    import subprocess
    rc = subprocess.run([sys.executable, str(ROOT / "tests" / "build_catalog.py"), "--check"],
                        capture_output=True, text=True)
    check(rc.returncode == 0,
          "catalog.js is in sync with projects.json (run build_catalog.py if this fails)")
    _ = json_ids

    print("== embedded engines are fully offline (no CDN) ==")
    for p in projects:
        if p.get("kind") == "engine":
            etext = (ROOT / p["embed"]).read_text(encoding="utf-8", errors="replace")
            ext = re.findall(r'src="https?://[^"]+|href="https?://[^"]+|@import\s+url\(https?://', etext)
            check(len(ext) == 0, f"engine '{p['id']}' has zero external CDN refs ({len(ext)} found)")
            if ext:
                for e in ext[:3]:
                    print("    ", e[:90])
    check((ROOT / "apps/vendor/plotly-2.27.0.min.js").is_file(), "Plotly vendored locally")
    for css in ("assets/fonts/pairwisepro.css", "assets/fonts/mafi.css"):
        fp = ROOT / css
        ok = fp.is_file() and "https://" not in fp.read_text(encoding="utf-8")
        check(ok, f"{css} vendored with no external URLs")

    print("== review fixes (security / a11y / R-correctness / robustness) ==")
    check('sandbox=' in html and "allow-scripts" in html, "engine iframe has a sandbox attribute")
    check('role="tabpanel"' in html, "panels expose role=tabpanel (a11y)")
    check('aria-controls=' in html, "tabs wire aria-controls (a11y)")
    check("PW70_CATALOG missing or malformed" in html, "hub guards against catalog.js load failure")
    # R-generation correctness (static signatures of the runtime template)
    check("ai = ai, bi = bi, ci = ci, di = di" in html, "count escalc passes ai/bi/ci/di args")
    check("m1i = m1i, sd1i = sd1i" in html, "continuous escalc passes m1i/sd1i/... args")
    check('measure = "PHR"' not in html and "PHR" not in html, "no invalid escalc PHR measure")
    check("log(dat$hr)" in html, "HR pooled via log-HR (no escalc HR measure)")
    check("qt(0.975, pi_df)" in html, "prediction interval uses t_{k-1} (matches the comment)")
    check("DerSimonian-Laird with k<10" in html, "small-k DL guard present")

    print("== license compliance ==")
    check((ROOT / "THIRD-PARTY-LICENSES.md").is_file(), "THIRD-PARTY-LICENSES.md present")
    for ofl in ("OFL-JetBrainsMono.txt", "OFL-PlusJakartaSans.txt", "OFL-Inter.txt"):
        fp = ROOT / "assets" / "fonts" / ofl
        ok = fp.is_file() and "SIL OPEN FONT LICENSE" in fp.read_text(encoding="utf-8", errors="replace").upper()
        check(ok, f"OFL license bundled: {ofl}")

    print("== story dashboard + e156 papers ==")
    check('data-panel="story"' in html, "Story panel present")
    check('id="panel-papers"' in html, "E156 Papers panel present")
    check('<script src="apps/vendor/chartkit.js">' in html, "hub loads the offline chart-kit")
    check('<script src="papers.js">' in html, "hub loads papers.js")
    for fid in ("figGauge", "figOutcome", "figKind", "figTags"):
        check(f'id="{fid}"' in html, f"chart slot {fid} present")
    check("data-refrain" in html, "story refrain present (narrative device)")
    check("Narrative method" in html, "secular narrative-method note present")
    # Secular-content guard: the storytelling must use techniques, not religious content.
    low = html.lower()
    religious = [w for w in ("allah", "quran", "qur'an", "surah", "verse ", "scripture", "holy", "prophet") if w in low]
    check(len(religious) == 0, f"no religious content in the page (found: {religious})")

    print("== chart-kit vendored offline ==")
    ck = ROOT / "apps" / "vendor" / "chartkit.js"
    check(ck.is_file(), "apps/vendor/chartkit.js present")
    if ck.is_file():
        ckt = ck.read_text(encoding="utf-8", errors="replace")
        ext = re.findall(r'src="https?://|href="https?://|import .*from .*https?://', ckt)
        check(len(ext) == 0, f"chart-kit has no external resource loads ({len(ext)})")
        check("window.ChartKit" in ckt or ")(window)" in ckt, "chart-kit exposes window.ChartKit")

    print("== e156 papers data + contract ==")
    pj = ROOT / "papers.js"
    check(pj.is_file(), "papers.js present")
    if pj.is_file():
        pt = pj.read_text(encoding="utf-8")
        check("window.PW70_PAPERS" in pt, "papers.js defines window.PW70_PAPERS")
        for pid in ("repro-floor-atlas", "pairwise70-dataset", "grma", "gwam", "pairwise70-workbench"):
            check(f'"{pid}"' in pt, f"paper present: {pid}")
        # The repro-floor results capsule must be a 7-sentence S1-S7 structure.
        sent = re.search(r'id:\s*"repro-floor-atlas".*?sentences:\s*\[(.*?)\]', pt, re.S)
        # each sentence sits on its own line ending in '"' (optionally a comma)
        n = len(re.findall(r'"\s*,?\s*\n', sent.group(1))) if sent else 0
        check(sent is not None and n == 7, f"repro-floor results capsule has 7 S-sentences (found {n})")

    print("== every project has required fields ==")
    for p in projects:
        ok = all(k in p for k in ("id", "name", "kind", "summary", "analysisTypes", "repo"))
        check(ok, f"project '{p.get('id','?')}' has required fields")

    return finish()


def finish():
    print(f"\n{CHECKS - len(FAILS)}/{CHECKS} checks passed.")
    if FAILS:
        print(f"FAILURES ({len(FAILS)}):")
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
