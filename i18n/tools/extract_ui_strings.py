#!/usr/bin/env python3
"""
Extract user-facing English strings from LimboAI editor sources.

The addon uses `TTR("...")` as the source-string lookup key. Those keys are the
msgids of the editor UI translation catalog (see i18n/ui/limboai.zh_CN.po).

Usage:
    python i18n/tools/extract_ui_strings.py            # print report
    python i18n/tools/extract_ui_strings.py --po FILE  # (re)generate PO template
    python i18n/tools/extract_ui_strings.py --check    # fail if PO is out of sync

Notes:
  * `TTR(vformat("...%s", ...))` is a bug for localization: the key would contain
    the substituted value. Such occurrences are reported and should be fixed in
    source to `vformat(TTR("...%s"), ...)`.
  * `TTR(U"...")` (char32_t literals) is supported.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRS = [
    "editor",
    "compat",
    "blackboard",
    "bt",
    "hsm",
    "util",
    "gdextension",
]

# TTR("...") / TTR(U"..."); captures the string literal contents.
TTR_RE = re.compile(r'\bTTR\(\s*(U?)"((?:[^"\\]|\\.)*)"')
# Unsafe pattern: TTR(vformat(...)) - key would include substituted values.
TTR_VFORMAT_RE = re.compile(r'\bTTR\(\s*vformat\(')

ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    '"': '"',
    "\\": "\\",
}


def unescape(literal: str) -> str:
    out = []
    i = 0
    while i < len(literal):
        ch = literal[i]
        if ch == "\\" and i + 1 < len(literal):
            nxt = literal[i + 1]
            out.append(ESCAPES.get(nxt, nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def iter_source_files():
    for d in SOURCE_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.cpp")):
            yield path
        for path in sorted(base.rglob("*.h")):
            yield path


def scan():
    """Return (entries, unsafe) where entries maps msgid -> sorted list of "file:line"."""
    entries: dict[str, set[str]] = {}
    unsafe: list[str] = []
    for path in iter_source_files():
        rel = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if TTR_VFORMAT_RE.search(line):
                unsafe.append(f"{rel}:{lineno}: {line.strip()}")
            for match in TTR_RE.finditer(line):
                msgid = unescape(match.group(2))
                entries.setdefault(msgid, set()).add(f"{rel}:{lineno}")
    return entries, unsafe


PO_HEADER = """\
msgid ""
msgstr ""
"Project-Id-Version: LimboAI 1.8.1 zh_CN\\n"
"Language: zh_CN\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"
"""


def po_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def po_unescape(text: str) -> str:
    return unescape(text)


def read_po(path: Path) -> dict[str, str]:
    """Very small PO reader: msgid -> msgstr (single line, unescaped)."""
    result: dict[str, str] = {}
    msgid: str | None = None
    msgstr: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("msgid "):
            msgid = po_unescape(line[len("msgid "):].strip('"'))
            msgstr = None
        elif line.startswith("msgstr ") and msgid is not None:
            msgstr = po_unescape(line[len("msgstr "):].strip('"'))
            result[msgid] = msgstr
            msgid = None
    return result


def write_po(path: Path, entries: dict[str, set[str]], existing: dict[str, str]):
    out = [PO_HEADER]
    for msgid in sorted(entries):
        for loc in sorted(entries[msgid]):
            out.append(f"#: {loc}\n")
        out.append(f'msgid "{po_escape(msgid)}"\n')
        out.append(f'msgstr "{po_escape(existing.get(msgid, ""))}"\n\n')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(out), encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--po", type=Path, help="PO file to (re)generate, keeping existing msgstr")
    ap.add_argument("--check", action="store_true", help="exit non-zero when PO is out of sync")
    args = ap.parse_args()

    entries, unsafe = scan()
    print(f"msgids: {len(entries)}")
    if unsafe:
        print(f"\nunsafe TTR(vformat(...)) occurrences: {len(unsafe)}")
        for item in unsafe:
            print("  " + item)

    if args.check:
        if not args.po:
            sys.exit("--check requires --po")
        existing = read_po(args.po)
        missing = sorted(set(entries) - set(existing))
        obsolete = sorted(set(existing) - set(entries) - {""})
        empty = sorted(k for k in entries if not existing.get(k))
        for title, items in (
            ("missing from PO", missing),
            ("obsolete in PO", obsolete),
            ("untranslated", empty),
        ):
            if items:
                print(f"\n{title}: {len(items)}")
                for item in items:
                    print("  " + item.replace("\n", "\\n"))
        sys.exit(1 if (missing or obsolete or empty) else 0)

    if args.po:
        existing = read_po(args.po) if args.po.exists() else {}
        write_po(args.po, entries, existing)
        print(f"wrote {args.po}")
        return

    for i, msgid in enumerate(sorted(entries), 1):
        print(f"{i:3d}. {msgid!r}")
        for loc in sorted(entries[msgid])[:3]:
            print(f"     @ {loc}")


if __name__ == "__main__":
    main()
