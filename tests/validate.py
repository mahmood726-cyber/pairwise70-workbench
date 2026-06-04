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
    # Exactly one real closing </script> tag; none leaked inside template literals.
    check(html.count("</script>") == 1, "exactly one literal </script> (no template leakage)")
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

    print("== inline CATALOG matches projects.json ==")
    inline_ids = set(re.findall(r'\{id:"([a-z0-9-]+)",\s*name:', html))
    check(inline_ids == json_ids,
          f"inline hub ids == projects.json ids (inline={len(inline_ids)}, json={len(json_ids)})")
    if inline_ids != json_ids:
        print("    diff:", inline_ids ^ json_ids)

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
