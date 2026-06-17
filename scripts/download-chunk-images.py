#!/usr/bin/env python3
"""Download product images for a single mirror chunk (og:image from HTML)."""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_LIST = ROOT / "data" / "archive-url-list.txt"
BASE = "https://aspriter.am"

OG_IMAGE = re.compile(r'<meta\s+property="og:image"\s+content="([^"]+)"', re.I)

_spec = importlib.util.spec_from_file_location(
    "download_snapshot", Path(__file__).parent / "download-snapshot.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_spec2 = importlib.util.spec_from_file_location(
    "download_images", Path(__file__).parent / "download-images.py"
)
_img = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_img)

load_cdx_map = _img.load_cdx_map
fallback_urls = _img.fallback_urls
download_with_timestamp = _img.download_with_timestamp


def image_urls_from_mirror(mirror: Path) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for html in mirror.rglob("*.html"):
        text = html.read_text(encoding="utf-8", errors="ignore")
        if 'og:type" content="product"' not in text and "page-product" not in text:
            continue
        for match in OG_IMAGE.findall(text):
            url = match if match.startswith("http") else f"{BASE}{match}"
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def main() -> None:
    parser = argparse.ArgumentParser(description="Download images for one mirror chunk")
    parser.add_argument("--mirror-dir", type=Path, default=None)
    parser.add_argument("--archive", type=Path, default=ARCHIVE_LIST)
    parser.add_argument("--snapshot", default=os.environ.get("SNAPSHOT_TIMESTAMP", "20230321042548"))
    parser.add_argument("--delay", type=float, default=float(os.environ.get("REQUEST_DELAY", "0.4")))
    args = parser.parse_args()

    mirror = args.mirror_dir or Path(os.environ.get("MIRROR_DIR", ROOT / "mirror"))
    if not mirror.exists():
        print(f"Mirror not found: {mirror}", file=sys.stderr)
        sys.exit(1)

    os.environ["MIRROR_DIR"] = str(mirror)
    targets: list[str] = []
    for url in image_urls_from_mirror(mirror):
        targets.extend(fallback_urls(url))
    # Deduplicate preserving order
    seen: set[str] = set()
    unique = []
    for u in targets:
        if u not in seen:
            seen.add(u)
            unique.append(u)

    cdx = load_cdx_map(args.archive) if args.archive.exists() else {}
    session = requests.Session()
    session.headers["User-Agent"] = "aspriter-restore/1.0 (Wayback restoration project)"

    print(f"Chunk images: {len(unique)} URLs in {mirror}", flush=True)
    ok = miss = 0
    for i, primary in enumerate(unique, 1):
        saved = False
        for candidate in fallback_urls(primary):
            if download_with_timestamp(session, candidate, cdx.get(candidate, ""), args.snapshot):
                ok += 1
                saved = True
                break
        if not saved:
            miss += 1
        if i % 25 == 0 or i == len(unique):
            print(f"  [{i}/{len(unique)}] {ok} ok, {miss} miss", flush=True)
        time.sleep(args.delay)

    print(f"Images done: {ok} ok, {miss} miss", flush=True)


if __name__ == "__main__":
    main()
