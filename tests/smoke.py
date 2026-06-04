#!/usr/bin/env python
"""Headless browser smoke test for the Pairwise70 Workbench hub.

Loads index.html via file://, exercises the tabs, gallery, engine select, and
the Reproduce run-record generator, and fails on top-document JS errors.
Run from repo root:  python tests/smoke.py
"""
import io
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "index.html").as_uri()
FAILS = []
TOTAL = 0


def expect(cond, msg):
    global TOTAL
    TOTAL += 1
    print(("  [PASS] " if cond else "  [FAIL] ") + msg)
    if not cond:
        FAILS.append(msg)


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,1000")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Chrome(options=opts)
    try:
        driver.set_page_load_timeout(60)
        driver.get(URL)
        wait = WebDriverWait(driver, 30)

        # Gallery renders cards
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#gallery .card")))
        cards = driver.find_elements(By.CSS_SELECTOR, "#gallery .card")
        expect(len(cards) >= 5, f"gallery rendered {len(cards)} project cards (>=5)")

        # Engine select populated
        opts_count = len(driver.find_elements(By.CSS_SELECTOR, "#engineSelect option"))
        expect(opts_count >= 2, f"engine select has {opts_count} engines (>=2)")

        # Switch to Reproduce tab and generate a run-record
        driver.find_element(By.CSS_SELECTOR, '[data-tab="reproduce"]').click()
        wait.until(EC.visibility_of_element_located((By.ID, "genRecord")))
        driver.find_element(By.ID, "genRecord").click()
        out_json = driver.find_element(By.ID, "outJson").text
        out_r = driver.find_element(By.ID, "outR").text
        expect("run-record@1" in out_json, "run-record JSON generated")
        expect("library(metafor)" in out_r, "metafor R script generated")
        expect("rma(yi, vi" in out_r, "R script pools with rma()")

        # Determinism: same seed -> identical PRNG probe across two generations
        import re
        from selenium.webdriver.support.ui import Select
        def probe():
            driver.find_element(By.ID, "genRecord").click()
            t = driver.find_element(By.ID, "outJson").text
            m = re.search(r'"prngProbe":\s*([0-9.]+)', t)
            return m.group(1) if m else None
        p1, p2 = probe(), probe()
        expect(p1 is not None and p1 == p2, f"seeded PRNG deterministic (probe {p1} == {p2})")

        # R-correctness: OR uses escalc with explicit args
        Select(driver.find_element(By.ID, "rMeasure")).select_by_visible_text("OR")
        driver.find_element(By.ID, "genRecord").click()
        r_or = driver.find_element(By.ID, "outR").text
        expect('escalc(measure = "OR", ai = ai, bi = bi, ci = ci, di = di' in r_or,
               "OR R script passes ai/bi/ci/di to escalc (runs)")
        expect("qt(0.975, pi_df)" in r_or, "PI computed as t_{k-1} explicitly")
        expect("predict(res, transf = exp)" in r_or, "ratio measure back-transformed via exp()")

        # R-correctness: HR avoids the invalid PHR measure
        Select(driver.find_element(By.ID, "rMeasure")).select_by_visible_text("HR")
        driver.find_element(By.ID, "genRecord").click()
        r_hr = driver.find_element(By.ID, "outR").text
        expect("log(dat$hr)" in r_hr and "PHR" not in r_hr, "HR pooled via log-HR, not escalc PHR")

        # Methodological guard: DL with small k surfaces a warning
        Select(driver.find_element(By.ID, "rModel")).select_by_value("DL")
        driver.find_element(By.ID, "rK").clear(); driver.find_element(By.ID, "rK").send_keys("5")
        driver.find_element(By.ID, "genRecord").click()
        warn = driver.find_element(By.ID, "reproWarn")
        rec = driver.find_element(By.ID, "outJson").text
        expect(warn.is_displayed() and "DerSimonian" in warn.text, "DL+small-k warning shown in UI")
        expect('"warnings"' in rec and "inputDigest" in rec, "manifest records warnings + inputDigest")

        # Keyboard a11y: ArrowRight moves tab selection
        driver.execute_script(
            "document.getElementById('tab-projects').focus();"
            "document.getElementById('tab-projects').dispatchEvent("
            "new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));")
        sel_analyze = driver.find_element(By.ID, "tab-analyze").get_attribute("aria-selected")
        expect(sel_analyze == "true", "ArrowRight key moves tab selection (a11y)")

        # Download buttons enabled after generation
        expect(driver.find_element(By.ID, "dlJson").is_enabled(), "Download JSON enabled")
        expect(driver.find_element(By.ID, "dlR").is_enabled(), "Download R enabled")

        # Fix #1 proof: load the engine directly and confirm Plotly resolves from the
        # local vendor file (no network). file:// can't reach a CDN, so if Plotly is
        # defined it came from apps/vendor/.
        engine_url = (ROOT / "apps" / "PairwisePro-v3.0-advanced.html").as_uri()
        driver.get(engine_url)
        time.sleep(1.5)
        plotly_type = driver.execute_script("return typeof window.Plotly;")
        expect(plotly_type in ("object", "function"),
               f"engine loads Plotly from local vendor offline (typeof Plotly = {plotly_type})")
        font_loaded = driver.execute_script(
            "return Array.from(document.styleSheets).some(s => (s.href||'').includes('pairwisepro.css'));")
        expect(bool(font_loaded), "engine loads vendored local font CSS")
        driver.get(URL)  # back to hub for log scan
        time.sleep(0.3)

        # Top-document JS errors only (ignore iframe/CDN network noise)
        sev = [l for l in driver.get_log("browser")
               if l["level"] == "SEVERE" and "index.html" in l.get("message", "")
               and "favicon" not in l.get("message", "")]
        expect(len(sev) == 0, f"no SEVERE top-document JS errors ({len(sev)} found)")
        for l in sev:
            print("    ", l["message"][:200])
    finally:
        driver.quit()

    print(f"\n{TOTAL - len(FAILS)}/{TOTAL} smoke checks passed.")
    if FAILS:
        print("SMOKE FAILURES:")
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("SMOKE PASSED")


if __name__ == "__main__":
    main()
