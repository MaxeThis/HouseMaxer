#!/usr/bin/env python3
"""Keep every Amazon link in this repo in step with parts/parts.json.

parts/parts.json holds the Amazon Associates tag and, for each part, a short
key and its ASIN. Links in the docs look like

    https://www.amazon.com/<key>/dp/<ASIN>?tag=<tag>

Amazon ignores the word before /dp/, so we use it to remember which part a
link is. That lets this script rewrite every link when you change the tag or
swap a part for a different listing. In a new doc you can also write AMZ:<key>
as a link target and the script fills it in.

    python3 tools/parts.py              # rewrite links + regenerate PARTS.md
    python3 tools/parts.py --check      # list links whose key isn't in parts.json
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "parts" / "parts.json").read_text())
TAG = DATA["tag"]
PARTS = {p["key"]: p for s in DATA["sections"] for p in s["items"]}

LINK = re.compile(r"https://www\.amazon\.com/([a-z0-9_]+)/dp/[A-Z0-9]{10}(?:\?tag=[\w-]+)?")
MARK = re.compile(r"AMZ:([a-z0-9_]+)")


def url(key):
    p = PARTS[key]
    if not p.get("asin"):
        return f"https://www.amazon.com/s?k={p['search'].replace(' ', '+')}&tag={TAG}"
    return f"https://www.amazon.com/{key}/dp/{p['asin']}?tag={TAG}"


def fix(text, missing):
    def sub(m):
        k = m.group(1)
        if k not in PARTS:
            missing.add(k)
            return m.group(0)
        return url(k)
    text = MARK.sub(sub, LINK.sub(sub, text))
    # search links (parts with no ASIN) carry the tag too
    return re.sub(r"(https://www\.amazon\.com/s\?k=[^&)\s]+&tag=)[\w-]+", lambda m: m.group(1) + TAG, text)


def parts_md():
    out = [
        "# Parts list",
        "",
        DATA["disclosure"],
        "",
        "Prices change daily; check the listing. **Buy used** marks the parts we",
        "think are worth buying used or refurbished (eBay, Amazon Renewed): they",
        "cost the most new and hold up well. Reset anything used to factory",
        "settings before you set it up.",
        "",
    ]
    for s in DATA["sections"]:
        out += [f"## {s['title']}", ""]
        if s.get("intro"):
            out += [s["intro"], ""]
        out += ["| Part | Why | Guide |", "|---|---|---|"]
        for p in s["items"]:
            name = f"[{p['name']}]({url(p['key'])})"
            if p.get("used"):
                name += " · **Buy used**"
            guide = f"[Guide {int(p['guide'].split('/')[-1].split('-', 1)[0])}]({p['guide']})" if p.get("guide") else ""
            out.append(f"| {name} | {p['why']} | {guide} |")
        out.append("")
    return "\n".join(out)


def main():
    missing = set()
    files = [f for f in ROOT.rglob("*.md") if "node_modules" not in f.parts]
    if "--check" not in sys.argv:
        (ROOT / "PARTS.md").write_text(parts_md())
    for f in files:
        t = f.read_text()
        n = fix(t, missing)
        if n != t and "--check" not in sys.argv:
            f.write_text(n)
    if missing:
        print("keys not in parts/parts.json:", ", ".join(sorted(missing)))
        sys.exit(1)
    print(f"ok: tag {TAG}, {len(PARTS)} parts, {len(files)} markdown files")


if __name__ == "__main__":
    main()
