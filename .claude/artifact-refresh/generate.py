#!/usr/bin/env python3
"""Re-bake the latest data.json into the shareable artifact HTML.

Reads ../../data.json (repo root) and injects it into template.html,
writing out.html. A scheduled Claude Code task then publishes out.html
to the existing artifact URL, keeping the same shareable link.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent  # project-status-dashboard/
DATA = REPO / "data.json"
TEMPLATE = HERE / "template.html"
OUT = HERE / "out.html"
PLACEHOLDER = "__DATA_JSON__"


def main() -> int:
    raw = DATA.read_text()
    # Validate it's real JSON so we never publish a broken snapshot.
    parsed = json.loads(raw)
    n = len(parsed.get("projects", []))
    template = TEMPLATE.read_text()
    if PLACEHOLDER not in template:
        print(f"ERROR: placeholder {PLACEHOLDER} missing from template.html", file=sys.stderr)
        return 1
    # json.dumps (not raw text) guarantees valid, safely-escaped JS.
    baked = template.replace(PLACEHOLDER, json.dumps(parsed, ensure_ascii=False, indent=2))
    OUT.write_text(baked)
    print(f"Wrote {OUT} with {n} projects (updated_at={parsed.get('updated_at')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
