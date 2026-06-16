#!/usr/bin/env python3
"""Clean mirrored HTML and rewrite asset URLs for local static hosting."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIRROR = ROOT / "mirror"
SITE = ROOT / "site"

# Wayback URL patterns to strip or rewrite
WAYBACK_PATTERNS = [
  # Full wayback URLs with modifiers
    re.compile(
        r"https?://web\.archive\.org/web/\d+(?:[a-z]{2}_)?/https?://(?:www\.)?aspriter\.am",
        re.I,
    ),
    re.compile(
        r"//web\.archive\.org/web/\d+(?:[a-z]{2}_)?/https?://(?:www\.)?aspriter\.am",
        re.I,
    ),
    re.compile(
        r"/web/\d+(?:[a-z]{2}_)?/https?://(?:www\.)?aspriter\.am",
        re.I,
    ),
]

# Internet Archive injected content
IA_SCRIPT = re.compile(
    r"<script[^>]*src=[\"']https?://web-static\.archive\.org[^\"']*[\"'][^>]*>\s*</script>",
    re.I,
)
IA_LINK = re.compile(
    r"<link[^>]*href=[\"']https?://web-static\.archive\.org[^\"']*[\"'][^>]*/?>",
    re.I,
)
IA_INLINE = re.compile(
    r"<script[^>]*>.*?__wm\.init.*?</script>",
    re.I | re.S,
)


def clean_html(content: str) -> str:
    content = IA_SCRIPT.sub("", content)
    content = IA_LINK.sub("", content)
    content = IA_INLINE.sub("", content)
    for pat in WAYBACK_PATTERNS:
        content = pat.sub("", content)
    # Normalize aspriter.am URLs to root-relative paths (avoid touching https://)
    content = re.sub(r"https?://(?:www\.)?aspriter\.am", "", content)
    # Protocol-relative URLs: //aspriter.am/path → /path
    content = re.sub(r"(?<![:/])//(?:www\.)?aspriter\.am", "", content)
    return content


def process_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8", errors="replace")
    dest.write_text(clean_html(text), encoding="utf-8")


def copy_binary(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser(description="Strip Wayback boilerplate from mirror")
    parser.add_argument("--input", type=Path, default=MIRROR)
    parser.add_argument("--output", type=Path, default=SITE)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    html_ext = {".html", ".htm"}
    count = 0
    for src in args.input.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(args.input)
        dest = args.output / rel
        if src.suffix.lower() in html_ext or src.name == "index.html":
            process_file(src, dest)
        else:
            copy_binary(src, dest)
        count += 1

    print(f"Processed {count} files → {args.output}/")


if __name__ == "__main__":
    main()
