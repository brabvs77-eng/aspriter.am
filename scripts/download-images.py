#!/usr/bin/env python3
"""Download product images referenced in products.json or mirrored HTML."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
MIRROR = ROOT / "mirror"
BASE = "https://aspriter.am"

_spec = importlib.util.spec_from_file_location(
    "download_snapshot", Path(__file__).parent / "download-snapshot.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
download = _mod.download


def image_urls_from_products(products_file: Path) -> list[str]:
    products = json.loads(products_file.read_text(encoding="utf-8"))
    urls: list[str] = []
    for p in products:
        if p.get("image"):
            urls.append(p["image"])
        for img in p.get("images") or []:
            urls.append(img if img.startswith("http") else f"{BASE}{img}")
    # Prefer large_default; also fetch home_default variant for listings
    expanded: list[str] = []
    seen: set[str] = set()
    for url in urls:
        for candidate in (url, url.replace("large_default", "home_default")):
            if candidate not in seen:
                seen.add(candidate)
                expanded.append(candidate)
    return expanded


def image_urls_from_mirror(mirror: Path) -> list[str]:
    pattern = re.compile(
        r'(?:https?://(?:www\.)?aspriter\.am)?(/[0-9]+-(?:large|home)_default[^"\'\s>]+\.(?:jpg|jpeg|png|webp))',
        re.I,
    )
    seen: set[str] = set()
    urls: list[str] = []
    for html in mirror.rglob("*.html"):
        for match in pattern.findall(html.read_text(encoding="utf-8", errors="ignore")):
            full = f"{BASE}{match}"
            if full not in seen:
                seen.add(full)
                urls.append(full)
    return urls


def main() -> None:
    parser = argparse.ArgumentParser(description="Download product images from Wayback")
    parser.add_argument("--products", type=Path, default=ROOT / "data" / "products.json")
    parser.add_argument("--mirror", type=Path, default=MIRROR)
    parser.add_argument("--from-mirror", action="store_true", help="Scan mirror HTML for image paths")
    parser.add_argument("--delay", type=float, default=float(os.environ.get("REQUEST_DELAY", "0.5")))
    args = parser.parse_args()

    if args.from_mirror and args.mirror.exists():
        targets = image_urls_from_mirror(args.mirror)
    elif args.products.exists():
        targets = image_urls_from_products(args.products)
    else:
        print("No products.json or mirror found.", file=sys.stderr)
        sys.exit(1)

    session = requests.Session()
    session.headers["User-Agent"] = "aspriter-restore/1.0 (Wayback restoration project)"

    print(f"Downloading {len(targets)} images...", flush=True)
    ok = 0
    for i, url in enumerate(targets, 1):
        if download(session, url, raw_html=False):
            ok += 1
        if i % 50 == 0 or i == len(targets):
            print(f"  [{i}/{len(targets)}] {ok} ok", flush=True)
        time.sleep(args.delay)

    print(f"\nDownloaded {ok}/{len(targets)} images.", flush=True)


if __name__ == "__main__":
    main()
