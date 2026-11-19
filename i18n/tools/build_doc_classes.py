#!/usr/bin/env python3
"""Build bilingual (Chinese + English) copies of the LimboAI class reference.

Source of truth:
  * doc_classes/*.xml          - upstream English class reference (never modified)
  * i18n/docs/docs_zh.json     - Chinese translations, keyed by class and field

Output:
  * gen/doc_classes_zh/*.xml   - same classes with Chinese added, English preserved

Bilingual layout (chosen so that the F1 class reference stays compact for short
entries and readable for long ones):

  brief_description:  "中文（English）"
  description / members / methods / signals / constants:
      - single-paragraph English shorter than INLINE_LIMIT characters:
            "中文（English）"
      - otherwise:
            中文段落...

            [b]English[/b]

            English paragraphs...

Usage:
    python i18n/tools/build_doc_classes.py \
        --json i18n/docs/docs_zh.json --src doc_classes --out gen/doc_classes_zh
    python i18n/tools/build_doc_classes.py --check   # report missing/unknown keys
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

INLINE_LIMIT = 200

ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

FIELD_TAGS = {
    "methods": "method",
    "members": "member",
    "constants": "constant",
    "signals": "signal",
}


def merge_text(zh: str, en: str, inline: bool) -> str:
    zh = zh.strip()
    en = en.strip()
    if not zh:
        return en
    if not en:
        return zh
    if inline or ("\n" not in en and len(en) <= INLINE_LIMIT):
        return f"{zh}（{en}）"
    return f"{zh}\n\n[b]English[/b]\n\n{en}"


def element_text(parent: ET.Element | None) -> str:
    if parent is None:
        return ""
    return "".join(parent.itertext()).strip()


def set_element_text(parent: ET.Element | None, text: str) -> None:
    if parent is None or not text:
        return
    # Keep a single text node, drop children (descriptions never have real children).
    for child in list(parent):
        parent.remove(child)
    parent.text = text


def description_target(node: ET.Element) -> ET.Element:
    """Methods/signals keep the text in a <description> child; members/constants own it."""
    child = node.find("description")
    return child if child is not None else node


def apply_class(root: ET.Element, data: dict) -> None:
    brief = root.find("brief_description")
    set_element_text(brief, merge_text(data.get("brief", ""), element_text(brief), inline=True))

    desc = root.find("description")
    set_element_text(desc, merge_text(data.get("desc", ""), element_text(desc), inline=False))

    for json_key, tag in FIELD_TAGS.items():
        container = root.find(json_key)
        if container is None:
            continue
        translations = data.get(json_key) or {}
        for node in container.findall(tag):
            name = node.get("name", "")
            if name not in translations:
                continue
            target = description_target(node)
            set_element_text(target, merge_text(translations[name], element_text(target), inline=False))


def collect_english(root: ET.Element) -> dict:
    """Return the English skeleton used to validate coverage of the JSON file."""
    out = {
        "brief": element_text(root.find("brief_description")),
        "desc": element_text(root.find("description")),
    }
    for json_key, tag in FIELD_TAGS.items():
        container = root.find(json_key)
        if container is None:
            continue
        entries = {}
        for node in container.findall(tag):
            entries[node.get("name", "")] = element_text(description_target(node))
        out[json_key] = entries
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--json",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs" / "docs_zh.json",
        help="Chinese translation JSON (default: i18n/docs/docs_zh.json)",
    )
    ap.add_argument("--src", type=Path, default=Path("doc_classes"))
    ap.add_argument("--out", type=Path, default=Path("gen/doc_classes_zh"))
    ap.add_argument("--check", action="store_true", help="only validate JSON coverage")
    args = ap.parse_args()

    if args.check:
        if not args.json:
            sys.exit("--check requires --json")
        translations = json.loads(args.json.read_text(encoding="utf-8"))
        translations.pop("_meta", None)
        problems = 0
        for xml_path in sorted(args.src.glob("*.xml")):
            class_name = ET.parse(xml_path).getroot().get("name")
            data = translations.get(class_name)
            if not data:
                print(f"missing class: {class_name}")
                problems += 1
                continue
            english = collect_english(ET.parse(xml_path).getroot())
            if not data.get("brief"):
                print(f"missing brief: {class_name}")
                problems += 1
            for key in ("methods", "members", "constants", "signals"):
                for name, text in english.get(key, {}).items():
                    if not text:
                        continue
                    if not (data.get(key) or {}).get(name):
                        print(f"missing {key}: {class_name}.{name}")
                        problems += 1
        unknown = set(translations) - {
            ET.parse(p).getroot().get("name") for p in args.src.glob("*.xml")
        }
        for name in sorted(unknown):
            print(f"unknown class in JSON: {name}")
            problems += 1
        print(f"{'OK' if problems == 0 else f'{problems} problem(s)'}")
        return 0 if problems == 0 else 1

    if not args.json or not args.json.exists():
        sys.exit(f"translation JSON not found: {args.json}")
    translations = json.loads(args.json.read_text(encoding="utf-8"))
    translations.pop("_meta", None)

    args.out.mkdir(parents=True, exist_ok=True)
    written = 0
    for xml_path in sorted(args.src.glob("*.xml")):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        class_name = root.get("name")
        data = translations.get(class_name)
        if data:
            apply_class(root, data)
            written += 1
        ET.indent(tree, space="\t")
        tree.write(args.out / xml_path.name, encoding="utf-8", xml_declaration=True)
    print(f"wrote {written}/{len(list(args.src.glob('*.xml')))} classes to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
