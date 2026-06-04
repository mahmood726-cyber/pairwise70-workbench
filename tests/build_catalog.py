#!/usr/bin/env python
"""Generate catalog.js from projects.json (the single source of truth).

projects.json is the ONE place to edit the catalog. The hub loads catalog.js via
a <script> tag (works under file://, unlike fetch). Run after editing projects.json:

    python tests/build_catalog.py            # write catalog.js
    python tests/build_catalog.py --check    # exit 1 if catalog.js is stale

validate.py runs the --check path so drift is impossible.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "projects.json"
OUT = ROOT / "catalog.js"
HEADER = "/* GENERATED from projects.json by tests/build_catalog.py - DO NOT EDIT BY HAND */\n"


def render():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    return HEADER + "window.PW70_CATALOG = " + json.dumps(data, indent=2, ensure_ascii=False) + ";\n"


def main():
    want = render()
    check = "--check" in sys.argv
    if check:
        have = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if have.replace("\r\n", "\n") == want.replace("\r\n", "\n"):
            print("catalog.js is in sync with projects.json")
            sys.exit(0)
        print("catalog.js is STALE - run: python tests/build_catalog.py")
        sys.exit(1)
    OUT.write_text(want, encoding="utf-8")
    print(f"wrote {OUT.name} ({len(want)} bytes) from projects.json")


if __name__ == "__main__":
    main()
