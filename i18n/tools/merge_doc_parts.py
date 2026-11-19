#!/usr/bin/env python3
"""Merge translated JSON parts into i18n/docs/docs_zh.json.

Usage:
    python i18n/tools/merge_doc_parts.py
    python i18n/tools/merge_doc_parts.py --check   # validate only

Parts are produced by the translation batches in i18n/docs/parts/*.json and are
merged in file-name order; conflicting entries are reported instead of silently
overwritten.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "i18n" / "docs" / "parts"
OUT = ROOT / "i18n" / "docs" / "docs_zh.json"

LIST_KEYS = ("methods", "members", "constants", "signals")


def load_parts() -> tuple[dict, list[str]]:
    merged: dict[str, dict] = {}
    problems: list[str] = []
    for part in sorted(PARTS.glob("*.json")):
        try:
            data = json.loads(part.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{part.name}: invalid JSON: {exc}")
            continue
        if not isinstance(data, dict):
            problems.append(f"{part.name}: top-level value is not an object")
            continue
        for class_name, entry in data.items():
            if class_name.startswith("_"):
                continue
            if not isinstance(entry, dict):
                problems.append(f"{part.name}: {class_name} is not an object")
                continue
            target = merged.setdefault(class_name, {})
            for key, value in entry.items():
                if key in LIST_KEYS and isinstance(value, dict):
                    bucket = target.setdefault(key, {})
                    for name, text in value.items():
                        if name in bucket and bucket[name] != text:
                            problems.append(f"{class_name}.{key}.{name}: conflicting translations")
                        bucket[name] = text
                elif isinstance(value, str):
                    if key in target and target[key] != value:
                        problems.append(f"{class_name}.{key}: conflicting translations")
                    target[key] = value
    return merged, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    merged, problems = load_parts()
    entries = sum(
        1 for entry in merged.values() for key in LIST_KEYS for _ in (entry.get(key) or {})
    )
    print(f"classes: {len(merged)}, list entries: {entries}")
    for problem in problems:
        print("  " + problem)

    if args.check:
        return 1 if problems else 0

    if not merged:
        sys.exit("no translated parts found")

    result = {
        "_meta": {
            "language": "zh_CN",
            "comment": "Chinese translations for doc_classes/*.xml. English originals live in doc_classes/.",
        }
    }
    for class_name in sorted(merged):
        result[class_name] = merged[class_name]

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
