#!/usr/bin/env python3
"""Bake data.json into the shareable board HTML.

Reads data.json + template.html (same folder by default) and writes out.html
with the data injected inline. A scheduled Claude routine then publishes
out.html to the same artifact URL, keeping the shareable link stable.

Usage:
    python3 generate.py [DATA_JSON] [TEMPLATE_HTML] [OUT_HTML]
Defaults: ./data.json  ./template.html  ./out.html
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PLACEHOLDER = "__DATA_JSON__"


def main(argv) -> int:
    data_path = pathlib.Path(argv[1]) if len(argv) > 1 else HERE / "data.json"
    template_path = pathlib.Path(argv[2]) if len(argv) > 2 else HERE / "template.html"
    out_path = pathlib.Path(argv[3]) if len(argv) > 3 else HERE / "out.html"

    raw = data_path.read_text()
    parsed = json.loads(raw)  # validate — never publish broken JSON
    n = len(parsed.get("projects", []))

    template = template_path.read_text()
    if PLACEHOLDER not in template:
        print(f"ERROR: placeholder {PLACEHOLDER} missing from {template_path}", file=sys.stderr)
        return 1

    baked = template.replace(PLACEHOLDER, json.dumps(parsed, ensure_ascii=False, indent=2))
    out_path.write_text(baked)
    print(f"Wrote {out_path} with {n} projects (updated_at={parsed.get('updated_at')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
