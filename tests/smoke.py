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


def expect(cond, msg):
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

        # Determinism: same seed -> identical determinismProbe across two generations
        import re
        def probe():
            driver.find_element(By.ID, "genRecord").click()
            t = driver.find_element(By.ID, "outJson").text
            m = re.search(r'"determinismProbe":\s*([0-9.]+)', t)
            return m.group(1) if m else None
        p1, p2 = probe(), probe()
        expect(p1 is not None and p1 == p2, f"seeded PRNG deterministic (probe {p1} == {p2})")

        # Download buttons enabled after generation
        expect(driver.find_element(By.ID, "dlJson").is_enabled(), "Download JSON enabled")
        expect(driver.find_element(By.ID, "dlR").is_enabled(), "Download R enabled")

        # Top-document JS errors only (ignore iframe/CDN network noise)
        sev = [l for l in driver.get_log("browser")
               if l["level"] == "SEVERE" and "index.html" in l.get("message", "")
               and "favicon" not in l.get("message", "")]
        expect(len(sev) == 0, f"no SEVERE top-document JS errors ({len(sev)} found)")
        for l in sev:
            print("    ", l["message"][:200])
    finally:
        driver.quit()

    print(f"\n{6 + 4 - len(FAILS)}/10 smoke checks passed.")
    if FAILS:
        print("SMOKE FAILURES:")
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("SMOKE PASSED")


if __name__ == "__main__":
    main()
